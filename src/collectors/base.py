"""
Base collector class defining the interface all collectors must implement.
"""
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Generator, Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CollectionError(Exception):
    """Raised when a collection fails fatally."""
    pass


class BaseCollector(ABC):
    """
    Abstract base class for all data source collectors.
    Provides common HTTP session, rate limiting, and retry logic.
    """

    DEFAULT_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 60))
    DEFAULT_MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
    DEFAULT_RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 5))
    USER_AGENT = os.environ.get(
        "USER_AGENT",
        "CannabisDataAggregator/1.0 (Open Data Collector)"
    )

    def __init__(self, source):
        """
        Args:
            source: DataSource ORM object or dict-like config object
        """
        self.source = source
        self.source_id = getattr(source, "source_id", str(source))
        self.logger = logging.getLogger(f"{__name__}.{self.source_id}")
        self._session: Optional[requests.Session] = None
        self._collected_count = 0
        self._last_request_time = 0.0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def collect(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yield records one at a time from the data source.
        Each record is a dict of raw field values.
        """
        raise NotImplementedError

    def test_connection(self) -> tuple[bool, str]:
        """
        Test if the source is accessible.
        Returns (success: bool, message: str)
        """
        try:
            url = self._get_url()
            params = self._get_initial_params()
            # Limit to 1 record for the test
            if params is not None:
                params = dict(params)
                if self.source.format == "soda":
                    params["$limit"] = 1
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return True, f"HTTP {resp.status_code} OK"
        except Exception as e:
            return False, str(e)

    def get_count(self) -> Optional[int]:
        """
        Get total record count from the source (if supported).
        Override in subclass for sources that support count queries.
        """
        return None

    # ------------------------------------------------------------------
    # HTTP session
    # ------------------------------------------------------------------

    @property
    def session(self) -> requests.Session:
        """Lazy-initialized requests session with retry logic."""
        if self._session is None:
            self._session = self._build_session()
        return self._session

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/csv, */*",
        })

        # Add API key header if configured
        api_key = self._get_api_key()
        if api_key and self.source.format == "soda":
            session.headers["X-App-Token"] = api_key
        elif api_key:
            env_name = getattr(self.source, "api_key_env", None)
            if env_name:
                session.headers["Authorization"] = f"Bearer {api_key}"

        # Add custom headers from config
        custom_headers = getattr(self.source, "headers", None) or {}
        if custom_headers:
            session.headers.update(custom_headers)

        # Retry adapter
        retry = Retry(
            total=self.DEFAULT_MAX_RETRIES,
            backoff_factor=self.DEFAULT_RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_url(self) -> str:
        """Get the primary URL for this source."""
        url = getattr(self.source, "url", None)
        if not url:
            raise CollectionError(f"No URL configured for source {self.source_id}")
        return url

    def _get_api_key(self) -> Optional[str]:
        """Get the API key from environment if configured."""
        env_name = getattr(self.source, "api_key_env", None)
        if env_name:
            return os.environ.get(env_name)
        return None

    def _get_initial_params(self) -> Optional[Dict[str, Any]]:
        """Get the initial query parameters."""
        params = getattr(self.source, "params", None) or {}
        return dict(params) if params else {}

    def _get_pagination_config(self) -> Optional[Dict[str, Any]]:
        """Get pagination configuration."""
        return getattr(self.source, "pagination", None) or {}

    def _rate_limit(self, rpm: int = 60) -> None:
        """Simple rate limiter: ensure minimum delay between requests."""
        if rpm <= 0:
            return
        min_interval = 60.0 / rpm
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def _get_rate_limit(self) -> int:
        """Get configured rate limit (requests per minute)."""
        return getattr(self.source, "rate_limit_rpm", None) or 60

    def _get_timeout(self) -> int:
        """Get configured request timeout."""
        return getattr(self.source, "timeout", None) or self.DEFAULT_TIMEOUT

    def fetch_url(
        self,
        url: str,
        params: Optional[Dict] = None,
        method: str = "GET",
        **kwargs
    ) -> requests.Response:
        """
        Fetch a URL with rate limiting and error handling.
        """
        self._rate_limit(self._get_rate_limit())
        self.logger.debug(f"Fetching: {url} params={params}")

        try:
            resp = self.session.request(
                method,
                url,
                params=params,
                timeout=self._get_timeout(),
                **kwargs
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            raise CollectionError(f"Request timed out after {self._get_timeout()}s: {url}")
        except requests.exceptions.ConnectionError as e:
            raise CollectionError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            raise CollectionError(f"HTTP error {e.response.status_code}: {url}")

    def close(self) -> None:
        """Clean up the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        return f"<{self.__class__.__name__} source={self.source_id}>"

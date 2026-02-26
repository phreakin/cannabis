"""
Collectors for JSON REST APIs and Socrata SODA APIs.
"""
import logging
from typing import Generator, Dict, Any, Optional, List

from .base import BaseCollector, CollectionError

logger = logging.getLogger(__name__)


class APICollector(BaseCollector):
    """
    Generic JSON REST API collector.
    Handles various pagination styles: offset, page, cursor, link-header.
    """

    def collect(self) -> Generator[Dict[str, Any], None, None]:
        """Yield records from the JSON API, handling pagination."""
        url = self._get_url()
        params = self._get_initial_params()
        pagination = self._get_pagination_config()

        pag_type = (pagination.get("type") or "none").lower()

        if pag_type == "none":
            yield from self._fetch_all_no_pagination(url, params)
        elif pag_type == "offset":
            yield from self._fetch_offset_paginated(url, params, pagination)
        elif pag_type == "page":
            yield from self._fetch_page_paginated(url, params, pagination)
        elif pag_type == "cursor":
            yield from self._fetch_cursor_paginated(url, params, pagination)
        elif pag_type == "link":
            yield from self._fetch_link_paginated(url, params, pagination)
        else:
            yield from self._fetch_all_no_pagination(url, params)

    def _fetch_all_no_pagination(
        self, url: str, params: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch entire response as single request."""
        resp = self.fetch_url(url, params=params or None)
        data = self._parse_json_response(resp)
        records = self._extract_records(data)
        for record in records:
            self._collected_count += 1
            yield record

    def _fetch_offset_paginated(
        self, url: str, params: dict, pagination: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch with offset/limit pagination."""
        limit_param = pagination.get("limit_param", "limit")
        offset_param = pagination.get("offset_param", "offset")
        page_size = int(pagination.get("page_size", 1000))

        params = dict(params or {})
        params[limit_param] = page_size
        offset = 0

        while True:
            params[offset_param] = offset
            resp = self.fetch_url(url, params=params)
            data = self._parse_json_response(resp)
            records = self._extract_records(data)

            if not records:
                break

            for record in records:
                self._collected_count += 1
                yield record

            if len(records) < page_size:
                break  # Last page

            offset += page_size
            self.logger.debug(
                f"Paginating: offset={offset}, fetched so far={self._collected_count}"
            )

    def _fetch_page_paginated(
        self, url: str, params: dict, pagination: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch with page number pagination."""
        page_param = pagination.get("page_param", "page")
        size_param = pagination.get("size_param", "per_page")
        page_size = int(pagination.get("page_size", 100))

        params = dict(params or {})
        params[size_param] = page_size
        page = pagination.get("start_page", 1)

        while True:
            params[page_param] = page
            resp = self.fetch_url(url, params=params)
            data = self._parse_json_response(resp)
            records = self._extract_records(data)

            if not records:
                break

            for record in records:
                self._collected_count += 1
                yield record

            if len(records) < page_size:
                break

            page += 1

    def _fetch_cursor_paginated(
        self, url: str, params: dict, pagination: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch with cursor-based pagination."""
        cursor_param = pagination.get("cursor_param", "cursor")
        cursor_field = pagination.get("cursor_field", "next_cursor")
        page_size = int(pagination.get("page_size", 100))
        size_param = pagination.get("size_param", "limit")

        params = dict(params or {})
        params[size_param] = page_size
        cursor = None

        while True:
            if cursor:
                params[cursor_param] = cursor

            resp = self.fetch_url(url, params=params)
            data = self._parse_json_response(resp)
            records = self._extract_records(data)

            for record in records:
                self._collected_count += 1
                yield record

            # Get next cursor from response metadata
            cursor = self._nested_get(data, cursor_field)
            if not cursor or not records:
                break

    def _fetch_link_paginated(
        self, url: str, params: dict, pagination: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch following Link: <next> HTTP headers."""
        next_url = url

        while next_url:
            resp = self.fetch_url(next_url, params=params)
            params = None  # Params are embedded in next_url after first request

            data = self._parse_json_response(resp)
            records = self._extract_records(data)

            for record in records:
                self._collected_count += 1
                yield record

            # Parse Link header for next page
            link_header = resp.headers.get("Link", "")
            next_url = self._parse_link_next(link_header)

    # ------------------------------------------------------------------
    # Response parsing helpers
    # ------------------------------------------------------------------

    def _parse_json_response(self, resp) -> Any:
        try:
            return resp.json()
        except ValueError as e:
            raise CollectionError(f"Failed to parse JSON response: {e}")

    def _extract_records(self, data) -> List[Dict]:
        """Extract the list of records from API response (handles various wrappers)."""
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            # Common wrapper patterns
            for key in ("data", "results", "records", "items", "features", "hits"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Try 'hits.hits' (Elasticsearch style)
            if "hits" in data and isinstance(data["hits"], dict):
                hits = data["hits"].get("hits", [])
                if isinstance(hits, list):
                    return [h.get("_source", h) for h in hits]

        return []

    def _nested_get(self, data: dict, key_path: str, default=None):
        """Get a nested value using dot notation (e.g., 'meta.next_cursor')."""
        keys = key_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            if current is None:
                return default
        return current

    def _parse_link_next(self, link_header: str) -> Optional[str]:
        """Parse Link header to find the 'next' URL."""
        if not link_header:
            return None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                url_part = part.split(";")[0].strip()
                return url_part.strip("<>")
        return None

    def get_count(self) -> Optional[int]:
        """Try to get total record count from API."""
        pagination = self._get_pagination_config()
        count_field = pagination.get("count_field") if pagination else None
        if not count_field:
            return None
        try:
            url = self._get_url()
            params = dict(self._get_initial_params() or {})
            params["$limit"] = 1
            resp = self.fetch_url(url, params=params)
            data = resp.json()
            if isinstance(data, dict):
                return self._nested_get(data, count_field)
        except Exception:
            pass
        return None


class SODACollector(APICollector):
    """
    Socrata Open Data API (SODA) collector.
    Handles Socrata-specific features:
    - App Token authentication (X-App-Token header)
    - SoQL query support ($where, $select, $order, $group)
    - $count endpoint for record totals
    - Built-in offset/limit pagination
    """

    SODA_LIMIT = 5000  # Socrata max per request

    def collect(self) -> Generator[Dict[str, Any], None, None]:
        """Yield records from SODA API with offset pagination."""
        url = self._get_url()
        params = dict(self._get_initial_params() or {})
        pagination = self._get_pagination_config() or {}
        page_size = int(pagination.get("page_size", self.SODA_LIMIT))

        params["$limit"] = page_size
        offset = 0

        while True:
            params["$offset"] = offset
            resp = self.fetch_url(url, params=params)

            try:
                records = resp.json()
            except ValueError:
                # Some Socrata portals return a UTF-8 BOM; strip it and retry
                try:
                    import json as _json
                    records = _json.loads(resp.content.decode("utf-8-sig"))
                except Exception as e:
                    raise CollectionError(f"SODA JSON parse error: {e}")

            if not isinstance(records, list):
                raise CollectionError(
                    f"Unexpected SODA response type: {type(records)}"
                )

            if not records:
                break

            for record in records:
                self._collected_count += 1
                yield record

            if len(records) < page_size:
                break  # Last page

            offset += page_size
            self.logger.debug(f"SODA pagination: offset={offset} total={self._collected_count}")

    def get_count(self) -> Optional[int]:
        """Get total count using SODA $count=true endpoint."""
        try:
            url = self._get_url()
            params = dict(self._get_initial_params() or {})
            params["$select"] = "count(*) AS count"
            params["$limit"] = 1
            params.pop("$offset", None)

            resp = self.fetch_url(url, params=params)
            data = resp.json()

            if isinstance(data, list) and data:
                count_val = data[0].get("count")
                if count_val is not None:
                    return int(count_val)
        except Exception as e:
            self.logger.debug(f"Could not get SODA count: {e}")
        return None

    def query(
        self,
        where: str = None,
        select: str = None,
        order: str = None,
        limit: int = None,
        offset: int = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute a SoQL query against this SODA source.
        Allows filtering, selecting, and ordering.
        """
        url = self._get_url()
        params = {}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        if order:
            params["$order"] = order
        if limit:
            params["$limit"] = limit
        if offset:
            params["$offset"] = offset

        resp = self.fetch_url(url, params=params)
        records = resp.json()
        for record in (records if isinstance(records, list) else []):
            yield record

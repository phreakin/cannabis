"""
CSV data collector - handles CSV and TSV downloads.
"""
import csv
import io
import logging
import os
import tempfile
from typing import Generator, Dict, Any, Optional

import chardet
import requests

from .base import BaseCollector, CollectionError

logger = logging.getLogger(__name__)


class CSVCollector(BaseCollector):
    """
    Collects data from CSV (or TSV) endpoints.
    Features:
    - Automatic encoding detection
    - Configurable delimiter
    - Header normalization
    - Streaming support for large files
    """

    def collect(self) -> Generator[Dict[str, Any], None, None]:
        """Yield records from the CSV file."""
        url = self._get_url()
        params = self._get_initial_params() or {}

        self.logger.info(f"Downloading CSV from: {url}")
        resp = self.fetch_url(url, params=params or None)

        # Detect encoding
        encoding = self._detect_encoding(resp)
        self.logger.debug(f"Detected encoding: {encoding}")

        # Detect delimiter
        delimiter = self._detect_delimiter(resp.content[:4096], encoding)
        self.logger.debug(f"Detected delimiter: {repr(delimiter)}")

        # Parse CSV
        try:
            text = resp.content.decode(encoding, errors="replace")
            reader = csv.DictReader(
                io.StringIO(text),
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
            )

            # Normalize headers
            if reader.fieldnames:
                reader.fieldnames = [
                    self._normalize_header(h) for h in reader.fieldnames
                ]

            for row in reader:
                # Clean up the row dict
                clean = {k: (v.strip() if isinstance(v, str) else v)
                         for k, v in row.items() if k}
                # Remove empty rows
                if any(v for v in clean.values()):
                    self._collected_count += 1
                    yield clean

        except Exception as e:
            raise CollectionError(f"CSV parsing error: {e}")

    def _detect_encoding(self, resp: requests.Response) -> str:
        """Detect character encoding from response."""
        # Try Content-Type header first
        content_type = resp.headers.get("Content-Type", "")
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()
            return charset

        # Use chardet for binary detection
        detected = chardet.detect(resp.content[:10000])
        if detected and detected.get("confidence", 0) > 0.7:
            return detected["encoding"] or "utf-8"

        return "utf-8"

    def _detect_delimiter(self, sample_bytes: bytes, encoding: str) -> str:
        """Auto-detect CSV delimiter from file sample."""
        try:
            sample = sample_bytes.decode(encoding, errors="replace")
            # Count common delimiters in first few lines
            lines = sample.split("\n")[:5]
            if not lines:
                return ","

            counts = {
                ",": sum(line.count(",") for line in lines),
                "\t": sum(line.count("\t") for line in lines),
                "|": sum(line.count("|") for line in lines),
                ";": sum(line.count(";") for line in lines),
            }
            return max(counts, key=counts.get)
        except Exception:
            return ","

    def _normalize_header(self, header: str) -> str:
        """Normalize column header to a clean identifier."""
        if not header:
            return "unknown"
        return (
            header.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("#", "num")
            .strip("_")
        )

    def collect_chunked(
        self,
        chunk_size: int = 10000
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Memory-efficient streaming collection for very large CSV files.
        Downloads to a temp file then streams parsing.
        """
        url = self._get_url()
        params = self._get_initial_params() or {}

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
            try:
                with self.session.get(
                    url, params=params or None,
                    stream=True, timeout=self._get_timeout()
                ) as resp:
                    resp.raise_for_status()
                    total_bytes = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                        total_bytes += len(chunk)
                    self.logger.info(f"Downloaded {total_bytes / 1024:.1f} KB to {tmp_path}")

                encoding = "utf-8"
                with open(tmp_path, "rb") as f:
                    detected = chardet.detect(f.read(10000))
                    if detected and detected.get("confidence", 0) > 0.7:
                        encoding = detected["encoding"] or "utf-8"

                with open(tmp_path, encoding=encoding, errors="replace") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        reader.fieldnames = [
                            self._normalize_header(h) for h in reader.fieldnames
                        ]
                    for row in reader:
                        clean = {k: (v.strip() if isinstance(v, str) else v)
                                 for k, v in row.items() if k}
                        if any(v for v in clean.values()):
                            self._collected_count += 1
                            yield clean

            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def get_count(self) -> Optional[int]:
        """Try to get line count by downloading the file (if small)."""
        return None  # Not efficient to count without downloading

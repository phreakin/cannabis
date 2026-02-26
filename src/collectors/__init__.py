from .base import BaseCollector
from .api_collector import APICollector, SODACollector
from .csv_collector import CSVCollector
from .geojson_collector import GeoJSONCollector

COLLECTOR_MAP = {
    "json": APICollector,
    "soda": SODACollector,
    "csv": CSVCollector,
    "geojson": GeoJSONCollector,
    "api": APICollector,
}


def get_collector(source) -> BaseCollector:
    """Factory: return the correct collector for a given DataSource."""
    fmt = (source.format or "json").lower()
    cls = COLLECTOR_MAP.get(fmt, APICollector)
    return cls(source)

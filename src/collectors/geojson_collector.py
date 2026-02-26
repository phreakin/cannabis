"""
GeoJSON collector - handles GeoJSON and Overpass API responses.
"""
import logging
from typing import Generator, Dict, Any, Optional

from .base import BaseCollector, CollectionError

logger = logging.getLogger(__name__)


class GeoJSONCollector(BaseCollector):
    """
    Collects data from GeoJSON endpoints.
    Extracts features from a GeoJSON FeatureCollection and flattens
    feature properties + geometry coordinates into a flat dict.
    """

    def collect(self) -> Generator[Dict[str, Any], None, None]:
        """Yield records from a GeoJSON source."""
        url = self._get_url()
        params = self._get_initial_params() or {}

        # Handle Overpass API (POST with data payload)
        if "overpass" in url.lower():
            yield from self._collect_overpass(url, params)
            return

        resp = self.fetch_url(url, params=params or None)

        try:
            geojson = resp.json()
        except ValueError as e:
            raise CollectionError(f"GeoJSON parse error: {e}")

        geojson_type = geojson.get("type", "")

        if geojson_type == "FeatureCollection":
            features = geojson.get("features", [])
            for feature in features:
                record = self._flatten_feature(feature)
                if record:
                    self._collected_count += 1
                    yield record

        elif geojson_type == "Feature":
            record = self._flatten_feature(geojson)
            if record:
                self._collected_count += 1
                yield record

        else:
            raise CollectionError(
                f"Unexpected GeoJSON type: {geojson_type}. "
                "Expected FeatureCollection or Feature."
            )

    def _collect_overpass(
        self, url: str, params: dict
    ) -> Generator[Dict[str, Any], None, None]:
        """Handle OpenStreetMap Overpass API queries."""
        query = params.get("data") or params.get("query", "")
        if not query:
            raise CollectionError("No Overpass query 'data' parameter configured.")

        self.logger.info(f"Running Overpass query: {query[:100]}...")
        resp = self.fetch_url(url, method="POST", data={"data": query})

        try:
            result = resp.json()
        except ValueError as e:
            raise CollectionError(f"Overpass response parse error: {e}")

        elements = result.get("elements", [])
        for element in elements:
            record = self._flatten_osm_element(element)
            if record:
                self._collected_count += 1
                yield record

    def _flatten_feature(self, feature: dict) -> Optional[Dict[str, Any]]:
        """
        Flatten a GeoJSON feature into a flat dict.
        Merges geometry coordinates and properties.
        """
        if not isinstance(feature, dict):
            return None

        record = {}

        # Extract properties
        props = feature.get("properties") or {}
        record.update(props)

        # Extract geometry
        geometry = feature.get("geometry") or {}
        geo_type = geometry.get("type")
        coords = geometry.get("coordinates")

        if geo_type == "Point" and coords and len(coords) >= 2:
            record["longitude"] = coords[0]
            record["latitude"] = coords[1]
            if len(coords) >= 3:
                record["elevation"] = coords[2]

        elif geo_type in ("Polygon", "MultiPolygon") and coords:
            # For polygon geometries, compute centroid as approximation
            centroid = self._polygon_centroid(coords, geo_type)
            if centroid:
                record["latitude"] = centroid[1]
                record["longitude"] = centroid[0]
            record["geometry_type"] = geo_type

        elif geo_type:
            record["geometry_type"] = geo_type

        return record if record else None

    def _flatten_osm_element(self, element: dict) -> Optional[Dict[str, Any]]:
        """
        Flatten an OpenStreetMap Overpass element into a flat dict.
        """
        record = {}

        # OSM tags contain the actual data
        tags = element.get("tags") or {}
        record.update(tags)

        # Element metadata
        record["osm_id"] = element.get("id")
        record["osm_type"] = element.get("type")  # node, way, relation

        # Coordinates (for nodes)
        if "lat" in element:
            record["latitude"] = element["lat"]
        if "lon" in element:
            record["longitude"] = element["lon"]

        # For ways/relations with center
        if "center" in element:
            center = element["center"]
            record["latitude"] = center.get("lat")
            record["longitude"] = center.get("lon")

        return record if record else None

    def _polygon_centroid(self, coordinates, geo_type: str) -> Optional[list]:
        """Approximate centroid of a polygon (first ring average)."""
        try:
            if geo_type == "Polygon":
                ring = coordinates[0]
            elif geo_type == "MultiPolygon":
                ring = coordinates[0][0]
            else:
                return None

            if not ring:
                return None

            lon = sum(p[0] for p in ring) / len(ring)
            lat = sum(p[1] for p in ring) / len(ring)
            return [lon, lat]
        except (IndexError, TypeError, ZeroDivisionError):
            return None

    def to_geojson_collection(self, records: list) -> dict:
        """
        Convert a list of collected records back to a GeoJSON FeatureCollection.
        Useful for exporting data with coordinates.
        """
        features = []
        for record in records:
            lat = record.get("latitude")
            lon = record.get("longitude")
            if lat is not None and lon is not None:
                props = {k: v for k, v in record.items()
                         if k not in ("latitude", "longitude")}
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": props
                })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    def get_count(self) -> Optional[int]:
        """GeoJSON doesn't typically have a count endpoint."""
        return None

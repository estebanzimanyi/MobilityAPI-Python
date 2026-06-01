"""Bulk ingestion helpers for a real-time fleet feed.

A city feed posts, on every tick, one (vehicleId, position, time) observation
per vehicle as a GeoJSON Point feature or a GeoParquet row. Each observation is
appended as one instant to that vehicle's moving feature, extending its
`tgeompoint` trajectory in `temporal_geometries`. The geometry and temporal work
run inside MobilityDB (ST_MakePoint / ST_GeomFromWKB, tgeompoint, appendInstant).
"""
import gzip
import io
import json
import re
import zlib


def decompress(body, content_encoding):
    """Transparently decode a compressed request body by its Content-Encoding.
    gzip and deflate use the standard library; br and zstd are supported when the
    optional library is installed.
    """
    enc = (content_encoding or "").lower().strip()
    if not enc or enc == "identity":
        return body
    if enc in ("gzip", "x-gzip"):
        return gzip.decompress(body)
    if enc == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            return zlib.decompress(body, -zlib.MAX_WBITS)  # raw deflate stream
    if enc == "br":
        import brotli
        return brotli.decompress(body)
    if enc == "zstd":
        import zstandard
        return zstandard.ZstdDecompressor().decompress(body)
    raise ValueError(f"unsupported Content-Encoding: {enc}")


def srid_from_crs(crs, default=4326):
    """Extract an EPSG code from an OGC CRS object/string (e.g. EPSG::25832)."""
    if not crs:
        return default
    text = crs if isinstance(crs, str) else json.dumps(crs)
    m = re.search(r"EPSG\D*?(\d{4,5})", text)
    return int(m.group(1)) if m else default


def _timestamp(feature, props):
    return (feature.get("when") or props.get("datetime") or props.get("timestamp")
            or props.get("time") or props.get("t"))


def parse_geojson_points(body):
    """A FeatureCollection of Point features, each with an id and a timestamp,
    into a list of {id, x, y, t} observations plus the SRID.
    """
    gj = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
    if gj.get("type") != "FeatureCollection":
        raise ValueError("bulk GeoJSON ingest expects a FeatureCollection")
    srid = srid_from_crs(gj.get("crs"))
    observations = []
    for feat in gj.get("features", []):
        if feat.get("type") != "Feature":
            continue
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            raise ValueError("bulk ingest expects Point geometries")
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            raise ValueError("a Point needs [x, y] coordinates")
        props = feat.get("properties") or {}
        ts = _timestamp(feat, props)
        if ts is None:
            raise ValueError("each feature needs a timestamp (properties.datetime)")
        fid = feat.get("id") if feat.get("id") is not None else props.get("id")
        if fid is None:
            raise ValueError("each feature needs an id (the vehicle identifier)")
        observations.append({"id": str(fid), "x": float(coords[0]), "y": float(coords[1]), "t": str(ts)})
    return observations, srid


def parse_geoparquet(body, geom_col="geometry", id_col="id", time_col="ts"):
    """A GeoParquet byte payload (one row per observation: WKB Point, id, ts) into
    {id, wkb, t} observations. The WKB is handed to PostGIS, not parsed here.
    """
    import pyarrow.parquet as pq
    table = pq.read_table(io.BytesIO(body))
    for col in (geom_col, id_col, time_col):
        if col not in table.column_names:
            raise ValueError(f"GeoParquet is missing the '{col}' column")
    geoms = table.column(geom_col).to_pylist()
    ids = table.column(id_col).to_pylist()
    times = table.column(time_col).to_pylist()
    observations = []
    for g, fid, ts in zip(geoms, ids, times):
        if not g:
            raise ValueError("GeoParquet row is missing the geometry")
        observations.append({"id": str(fid), "wkb": bytes(g), "t": str(ts)})
    return observations, 4326


# one instant appended to a tgeompoint trajectory; the point comes either from
# x/y (GeoJSON) or from WKB handed to PostGIS (GeoParquet)
_INST_XY = "tgeompoint(ST_SetSRID(ST_MakePoint(%s, %s), %s), %s::timestamptz)"
_INST_WKB = "tgeompoint(ST_SetSRID(ST_GeomFromWKB(%s), %s), %s::timestamptz)"


def _instant(observation, srid):
    if "wkb" in observation:
        return _INST_WKB, (observation["wkb"], srid, observation["t"])
    return _INST_XY, (observation["x"], observation["y"], srid, observation["t"])


def ensure_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moving_features (
            id TEXT PRIMARY KEY,
            collection_id TEXT REFERENCES collections(id) ON DELETE CASCADE,
            type TEXT DEFAULT 'Feature',
            geometry geometry, properties JSONB, bbox JSONB,
            time_range TSTZRANGE, crs JSONB, trs JSONB,
            created_at TIMESTAMP DEFAULT NOW())""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temporal_geometries (
            id SERIAL PRIMARY KEY,
            feature_id TEXT REFERENCES moving_features(id) ON DELETE CASCADE,
            collection_id TEXT REFERENCES collections(id) ON DELETE CASCADE,
            geometry_type TEXT, geometry geometry, trajectory tgeompoint,
            interpolation TEXT, base JSONB,
            created_at TIMESTAMP DEFAULT NOW())""")


def append_observations(cursor, collection_id, observations, srid):
    """Append each observation as one instant, creating the feature/trajectory on
    first sight and extending it with appendInstant afterwards. Runs inside the
    caller's transaction so the whole batch commits atomically.
    """
    created, extended = set(), 0
    for o in observations:
        inst, args = _instant(o, srid)
        cursor.execute(
            "INSERT INTO moving_features (id, collection_id, type) VALUES (%s, %s, 'Feature') "
            "ON CONFLICT (id) DO NOTHING RETURNING id", (o["id"], collection_id))
        if cursor.fetchone() is not None:
            created.add(o["id"])
        cursor.execute(
            f"UPDATE temporal_geometries SET trajectory = appendInstant(trajectory, {inst}) "
            "WHERE feature_id = %s RETURNING id", (*args, o["id"]))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO temporal_geometries "
                "(feature_id, collection_id, geometry_type, trajectory, interpolation) "
                f"VALUES (%s, %s, 'MovingPoint', {inst}, 'Linear')",
                (o["id"], collection_id, *args))
        extended += 1
    return {"observations": extended, "featuresCreated": len(created),
            "featuresExtended": extended - len(created)}

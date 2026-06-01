# GET /collections/{collectionId}/export
# Lakehouse bulk feed. Default is NDJSON (one Feature per line, the temporal
# geometry as MF-JSON), streamed from a server-side cursor so memory is bounded
# regardless of collection size. ?format=parquet emits the columnar WKB + a
# bbox/time sidecar (xmin..tmax) that a lake consumer (DuckDB / MobilityDuck /
# Spark) can prune by space and time before decoding geometry.
import io
import json
from urllib.parse import urlparse, parse_qs

from utils import handle_error

_NDJSON_SQL = """
    SELECT mf.id,
           coalesce(mf.properties, '{}'::jsonb)::text,
           asMFJSON(tg.trajectory)
    FROM moving_features mf
    LEFT JOIN temporal_geometries tg
           ON mf.id = tg.feature_id AND mf.collection_id = tg.collection_id
    WHERE mf.collection_id = %s
    ORDER BY mf.id
"""

_PARQUET_SQL = """
    SELECT mf.id,
           coalesce(mf.properties, '{}'::jsonb)::text,
           asBinary(tg.trajectory),
           Xmin(stbox(tg.trajectory)), Ymin(stbox(tg.trajectory)),
           Xmax(stbox(tg.trajectory)), Ymax(stbox(tg.trajectory)),
           Tmin(stbox(tg.trajectory))::text, Tmax(stbox(tg.trajectory))::text
    FROM moving_features mf
    LEFT JOIN temporal_geometries tg
           ON mf.id = tg.feature_id AND mf.collection_id = tg.collection_id
    WHERE mf.collection_id = %s
    ORDER BY mf.id
"""


def export_collection(self, collection_id, connection, cursor):
    cursor.execute("SELECT id FROM collections WHERE id = %s", (collection_id,))
    if cursor.fetchone() is None:
        handle_error(self, 404, f"Collection '{collection_id}' not found")
        return

    fmt = parse_qs(urlparse(self.path).query).get("format", ["ndjson"])[0]
    if fmt == "parquet":
        _export_parquet(self, collection_id, connection)
    else:
        _export_ndjson(self, collection_id, connection)


def _export_ndjson(self, collection_id, connection):
    self.send_response(200)
    self.send_header("Content-Type", "application/x-ndjson")
    self.end_headers()
    stream = connection.cursor(name="mfapi_export_nd")
    stream.itersize = 1000
    try:
        stream.execute(_NDJSON_SQL, (collection_id,))
        for fid, properties, tgeom in stream:
            feature = {
                "type": "Feature",
                "id": fid,
                "properties": json.loads(properties),
                "temporalGeometry": json.loads(tgeom) if tgeom else None,
            }
            self.wfile.write((json.dumps(feature) + "\n").encode("utf-8"))
    finally:
        stream.close()


def _export_parquet(self, collection_id, connection):
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema([
        ("id", pa.string()), ("properties", pa.string()), ("trajectory_wkb", pa.binary()),
        ("xmin", pa.float64()), ("ymin", pa.float64()), ("xmax", pa.float64()), ("ymax", pa.float64()),
        ("tmin", pa.string()), ("tmax", pa.string()),
    ])
    rowgroup = 1024
    sink = io.BytesIO()
    writer = pq.ParquetWriter(sink, schema)
    stream = connection.cursor(name="mfapi_export_pq")
    stream.itersize = rowgroup
    cols = {name: [] for name in schema.names}

    def flush():
        if not cols["id"]:
            return
        # one row group per batch: the pyarrow working set is bounded by rowgroup,
        # and each row group carries its own min/max statistics for pushdown.
        writer.write_table(pa.table(cols, schema=schema))
        for name in cols:
            cols[name].clear()

    try:
        stream.execute(_PARQUET_SQL, (collection_id,))
        for fid, props, wkb, xmin, ymin, xmax, ymax, tmin, tmax in stream:
            cols["id"].append(fid)
            cols["properties"].append(props)
            cols["trajectory_wkb"].append(bytes(wkb) if wkb is not None else None)
            cols["xmin"].append(xmin); cols["ymin"].append(ymin)
            cols["xmax"].append(xmax); cols["ymax"].append(ymax)
            cols["tmin"].append(tmin); cols["tmax"].append(tmax)
            if len(cols["id"]) >= rowgroup:
                flush()
        flush()
    finally:
        stream.close()
        writer.close()

    self.send_response(200)
    self.send_header("Content-Type", "application/vnd.apache.parquet")
    self.send_header("Content-Disposition", f'attachment; filename="{collection_id}.parquet"')
    self.end_headers()
    self.wfile.write(sink.getvalue())

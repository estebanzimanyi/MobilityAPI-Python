# GET /collections/{collectionId}/export
# Lakehouse bulk feed: the collection's moving features streamed as NDJSON (one
# Feature per line, the temporal geometry as MF-JSON) from a server-side cursor,
# so memory is bounded regardless of collection size. A lake consumer (DuckDB /
# MobilityDuck / Spark) ingests the stream directly.
import json

from utils import handle_error


def export_collection(self, collection_id, connection, cursor):
    cursor.execute("SELECT id FROM collections WHERE id = %s", (collection_id,))
    if cursor.fetchone() is None:
        handle_error(self, 404, f"Collection '{collection_id}' not found")
        return

    self.send_response(200)
    self.send_header("Content-Type", "application/x-ndjson")
    self.end_headers()

    # Server-side cursor: rows are fetched in batches, so a large collection
    # streams at bounded memory.
    stream = connection.cursor(name="mfapi_export")
    stream.itersize = 1000
    try:
        stream.execute(
            """
            SELECT mf.id,
                   coalesce(mf.properties, '{}'::jsonb)::text,
                   asMFJSON(tg.trajectory)
            FROM moving_features mf
            LEFT JOIN temporal_geometries tg
                   ON mf.id = tg.feature_id AND mf.collection_id = tg.collection_id
            WHERE mf.collection_id = %s
            ORDER BY mf.id
            """,
            (collection_id,),
        )
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

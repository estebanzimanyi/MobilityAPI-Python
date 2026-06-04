# Bulk ingestion of a real-time fleet feed (extension, not in conformsTo):
# POST /collections/{collectionId}/bulk
#
# The body is a batch of (vehicleId, position, time) observations encoded as
# GeoJSON (a FeatureCollection of Point features) or GeoParquet (one row per
# observation), optionally compressed via Content-Encoding (gzip, deflate, br,
# zstd). Each observation is appended as one instant to the matching moving
# feature's trajectory, creating the feature on first sight. The whole batch
# commits atomically.
import json

from resource.bulk.bulk_helper import (
    decompress, parse_geojson_points, parse_geoparquet, ensure_tables, append_observations)


def post_bulk(self, collection_id, connection, cursor):
    try:
        cursor.execute("SELECT id FROM collections WHERE id = %s", (collection_id,))
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = decompress(raw, self.headers.get("Content-Encoding"))
        except ValueError as e:
            self.handle_error(415, str(e))
            return
        except ImportError as e:
            self.handle_error(415, f"Content-Encoding needs an optional library: {e}")
            return

        ctype = (self.headers.get("Content-Type") or "").lower()
        if "parquet" in ctype:
            observations, srid = parse_geoparquet(body)
            fmt = "geoparquet"
        else:
            observations, srid = parse_geojson_points(body)
            fmt = "geojson"

        ensure_tables(cursor)
        summary = append_observations(cursor, collection_id, observations, srid)
        connection.commit()

        summary.update({"collection": collection_id, "format": fmt, "srid": srid})
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(summary).encode("utf-8"))

    except ValueError as e:
        connection.rollback()
        self.handle_error(400, str(e))
    except Exception as e:
        connection.rollback()
        msg = str(e)
        if "increasing" in msg or "overlap" in msg.lower() or "ordered" in msg.lower():
            self.handle_error(409, f"an observation is not strictly after the feature's last instant: {msg}")
        else:
            self.handle_error(500, f"Internal server error: {msg}")

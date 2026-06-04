# REQ 32: /req/movingfeatures/tpgeometry-query
# REQ 33: /req/movingfeatures/tpgeometry-query-success
# SECTION 8.7.3. Distance Query
from utils import send_json_response
from resource.temporal_geom_query.query_helper import build_query_response
import json
import traceback
from datetime import datetime

#    GET /collections/{collectionId}/items/{featureId}/tgsequence/{geometryId}/distance
def get_distance(self, collection_id, feature_id, geometry_id, connection, cursor):
    try:
        #collection exists
        cursor.execute(
            "SELECT id FROM collections WHERE id = %s",
            (collection_id,)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        
        #feature exists
        cursor.execute(
            "SELECT id FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Feature '{feature_id}' not found in collection '{collection_id}'")
            return
        
        # {geometry_id} is the 1-based index of a member sequence of the trajectory
        try:
            member = int(geometry_id)
        except (TypeError, ValueError):
            self.handle_error(400, "invalid temporal geometry id (1-based index into the sequence)")
            return
        cursor.execute("""
            SELECT 1 FROM temporal_geometries
            WHERE feature_id = %s AND collection_id = %s
              AND %s BETWEEN 1 AND numSequences(trajectory)
        """, (feature_id, collection_id, member))
        if cursor.fetchone() is None:
            self.handle_error(404, f"Temporal geometry '{geometry_id}' not found for feature '{feature_id}'")
            return
##############################################################################################################################

# API returns derived time-to-distance curve data from all available time of the specified TemporalPrimitiveGeometry object ref ogc p65
        cursor.execute("""
            SELECT
            getTimestamp(unnest(instants(round(cumulativeLength(sequenceN(trajectory, %s)),6)))) as time,
            getValue(unnest(instants(round(cumulativeLength(sequenceN(trajectory, %s)),6)))) as distance
            FROM temporal_geometries
            WHERE feature_id = %s AND collection_id = %s
        """, (member, member, feature_id, collection_id))
        #eg t[0@08:00, 14.1@08:01, 27.1@08:02, 42.4@08:03] clean ?
        rows = cursor.fetchall()
        if not rows:
            self.handle_error(404, f"Temporal geometry '{geometry_id}' not found for feature '{feature_id}'")
            return
        
        values = {
            "datetimes": [
                t.isoformat() if hasattr(t, "isoformat") else str(t)
                for t, d in rows
            ],
            "values": [
                float(d)
                for t, d in rows
            ]
        }
                #response
        base_url = f"http://{self.server.server_name}:{self.server.server_port}"
        path = f"/collections/{collection_id}/items/{feature_id}/tgsequence/{geometry_id}/distance"
        
        response = build_query_response(
            values=values,
            unit="meters",
            query_type="distance",
            base_url=base_url,
            path=path
        )
        
        send_json_response(self, 200, response)
        
    except Exception as e:
        connection.rollback()
        # print(f"Error in distance query: {e}")
        # traceback.print_exc()
        self.handle_error(500, f"Internal server error: {str(e)}")
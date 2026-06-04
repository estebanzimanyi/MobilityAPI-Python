# REQ 32: /req/movingfeatures/tpgeometry-query
# REQ 33: /req/movingfeatures/tpgeometry-query-success
# SECTION 8.7.4. Velocity Query
from utils import send_json_response
from resource.temporal_geom_query.query_helper import build_query_response
import json
import traceback
from datetime import datetime

#GET /collections/{collectionId}/items/{featureId}/tgsequence/{geometryId}/velocity
def get_velocity(self, collection_id, feature_id, geometry_id, connection, cursor):
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
#speed of the addressed member sequence
        cursor.execute("""
        SELECT
            getTimestamp(unnest(instants(speed(sequenceN(trajectory, %s))))) as time,
            getValue(unnest(instants(speed(sequenceN(trajectory, %s))))) as speed
            FROM temporal_geometries
            WHERE feature_id = %s AND collection_id = %s
        """, (member, member, feature_id, collection_id))
        rows = cursor.fetchall()
                
        if not rows:
            self.handle_error(404, f"No velocity data found for geometry '{geometry_id}'")
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
        path = f"/collections/{collection_id}/items/{feature_id}/tgsequence/{geometry_id}/velocity"
        
        response = build_query_response(
            values=values,
            unit="m/s",
            query_type="velocity",
            base_url=base_url,
            path=path
        )
        
        send_json_response(self, 200, response)
        
    except Exception as e:
        connection.rollback()
        # print(f"Error in velocity query: {e}", flush=True)
        # traceback.print_exc()
        self.handle_error(500, f"Internal server error: {str(e)}")
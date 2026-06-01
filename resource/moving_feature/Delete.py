# REQ20: /req/movingfeatures/mf-delete
# REQ22: /req/movingfeatures/mf-delete-success

from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import send_json_response
from psycopg2 import sql
import json

def delete_single_moving_feature(self, collection_id, feature_id, connection, cursor):
    try:
        # collection exists?
        cursor.execute(
            "SELECT id FROM collections WHERE id = %s",
            (collection_id,)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        #check ,clean currently creating the moving_features table in moving_features Post, so there is a possibility yhe collection is there  but not moving_features --> maybe it's better to create this table on collection creation- for npow everything is caught by exceptioon
        cursor.execute("""
            DELETE FROM moving_features 
            WHERE id = %s AND collection_id = %s
            RETURNING id
        """, (feature_id, collection_id))
        
        deleted = cursor.fetchone()
        connection.commit()

        if not deleted:
            self.handle_error(404, f"Feature '{feature_id}' not found in collection '{collection_id}'")
            return
        
        # Req 22 code 204 
        self.send_response(204)
        self.end_headers()

    except Exception as e:
        connection.rollback()
        # print(f"Error deleting feature: {e}")
        self.handle_error(500, f"Internal server error: {str(e)}")
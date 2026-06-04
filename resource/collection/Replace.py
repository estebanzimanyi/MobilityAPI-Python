# REQ7: /req/mf-collection/collection-put
# RE10: /req/mf-collection/collection-put-success

from http.server import BaseHTTPRequestHandler, HTTPServer
from resource.collection.collection_helper import (
    validate_collection_data,
    collection_exists,
    update_collection
)
import json

def put_collection(self, collection_id, connection, cursor):
    try:
        content_length = int(self.headers.get('Content-Length', 0))
        put_data = self.rfile.read(content_length)
        data_dict = json.loads(put_data)
        
        # Check if collection exists
        if not collection_exists(cursor, collection_id):
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        
        # validate replace attributes for collection
        errors, validated_data = validate_collection_data(data_dict, is_update=True)
        if errors:
            self.handle_error(400, "; ".join(errors))
            return
        
        # Update collection
        updated = update_collection(cursor, collection_id, validated_data)
        connection.commit()
        
        if updated:
            self.send_response(204)
        else:
            # no changes 
            self.send_response(204)
        self.end_headers()
        
    except json.JSONDecodeError:
        self.handle_error(400, "Invalid JSON")
    except Exception as e:
        connection.rollback()
        print(f"Error in put_collection: {e}")
        self.handle_error(500, f"Internal server error: {str(e)}")
# REQ6: /req/mf-collection/collection-get
# REQU 9: /req/mf-collection/collection-get-success

from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import send_json_response
from resource.collection.collection_helper import (
    fetch_collection_by_id,
    build_collection_response
)
import json
# clean : use this in collections/retrieve.py?
def get_collection_id(self, collection_id, connection, cursor):
    try:
        collection = fetch_collection_by_id(cursor, collection_id)
        
        if not collection:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        
        base_url = f"http://{self.server.server_name}:{self.server.server_port}"
        
        # Build response 
        response = build_collection_response(collection, base_url)
        
        send_json_response(self, 200, response)
        
    except Exception as e:
        print(f"Error in get_collection_id: {e}")
        self.handle_error(500, f"Internal server error: {str(e)}")
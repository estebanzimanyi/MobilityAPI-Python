# REQ1: /req/mf-collection/collections-get
# REQ 3: /req/mf-collection/collections-get-success
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import send_json_response
import json
from resource.collection.collection_helper import (
    fetch_all_collections,
    build_collection_response,
    build_collections_list_response
)


def get_collections(self, connection, cursor):
    try:
        collections_data = fetch_all_collections(cursor)
        
        base_url = f"http://{self.server.server_name}:{self.server.server_port}"
        collections_list = []
        
        # Build each collection resp
        for collection in collections_data:
            collections_list.append(build_collection_response(collection, base_url))
        
        #final resp
        response = build_collections_list_response(collections_list, base_url)
        
        send_json_response(self, 200, response)
        
    except Exception as e:
        print(f"Error in get_collections: {e}")
        self.handle_error(500, f"Internal server error: {str(e)}")
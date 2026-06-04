from http.server import BaseHTTPRequestHandler, HTTPServer
import json


def column_discovery(collectionId, cursor):
    sqlString = f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS where table_name = '{collectionId}';"
    cursor.execute(sqlString)
    rs = cursor.fetchall()
    return rs


def column_discovery2(collectionId, cursor):
    sqlString = f"SELECT column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS where  table_name = '{collectionId}';"
    cursor.execute(sqlString)
    rs = cursor.fetchall()
    return rs

def send_json_response(handler, status_code, data=None):
    handler.send_response(status_code)
    handler.send_header("Content-type", "application/json")
    handler.end_headers()
    if data is None:
     return

    # if data is dict,!!> json
    if isinstance(data, dict):
        data = json.dumps(data)
    
    # encode  data utf8
    handler.wfile.write(data.encode('utf-8'))

def handle_error(handler, code, message):
    error_response = {
        "code": str(code),
        "description": message
    }
    send_json_response(handler, code, error_response)
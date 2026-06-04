import pytest
import requests
import json
from pymeos import *
import json
from datetime import datetime
# loggerto JSON
API_LOGS = []

def log_to_json(action, response):
    req = response.request
    

    req_body = None
    if req.body:
        try:
            req_body = json.loads(req.body)
        except:
            req_body = str(req.body)[:500]
    
    resp_body = None
    try:
        resp_body = response.json()
    except:
        resp_body = response.text[:500] if response.text else None
    
    API_LOGS.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "url": req.url,
        "method": req.method,
        "status": response.status_code,
        "request_body": req_body,
        "response_body": resp_body
    })
    
    # save to file
    with open("api_logs.json", "w") as f:
        json.dump(API_LOGS, f, indent=2)


def log_request_response(action: str, response: requests.Response):

    req = response.request
    print(f"\n===| {action.upper()} |===")
    print(f"==> {req.method} {req.url}")
    if req.body:
        try:
            body = json.loads(req.body)
            print("Request JSON:", json.dumps(body, indent=2)[:500])
        except Exception:
            print("Request body:", req.body[:500])
    print(f"<== Status: {response.status_code}")
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2)[:500])
    except Exception:
        print("Response Text:", response.text[:500])
    print("=" * 60 + "\n")

    log_to_json(action, response)







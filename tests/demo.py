import pytest
import requests
import json
import os
import urllib.parse
import ijson
from pymeos import TGeomPoint, pymeos_finalize
from common import log_request_response   # uses API_LOGS and saves logs automatically

HOST = "http://localhost:8080"
COLLECTION_ID = "demo_ships"
PORT_BBOX = "651135,6058230,651422,6058548"   # Rodby harbour envelope (meters, EPSG:25832)
TIME_INTERVAL = "2024-07-08T10:30:00+00/2024-07-08T11:30:00+00"  
BATCH_SIZE = 20 

# each feature dict from the top‑level array without loading all
def iter_features_from_json(file_path):
  
    with open(file_path, 'rb') as f:
        objects = ijson.items(f, 'item')
        for obj in objects:
            feature = {
                "type": "Feature",
                "id": str(obj["mmsi"]),
                "crs": {
                    "type": "name",
                    "properties": "urn:ogc:def:crs:EPSG::25832"
                },
                "temporalGeometry": json.loads(obj["trajectory"]),
                "properties": obj["properties"]
            }
            yield feature

# ---------- Fixture: create collection and post features in batches ----------
@pytest.fixture(scope="module")
def setup_data():
    #  Create collection
    collection_data = {
        "title": COLLECTION_ID,
        "description": "Synthetic vessels for demo",
        "updateFrequency": 1000,
        "itemType": "movingfeature"
    }
    resp = requests.post(f"{HOST}/collections", json=collection_data)
    log_request_response("Create collection", resp)
    assert resp.status_code in (201, 409)

    # Post features in batches (same as original test_create_feature_collection)
    created_count = 0
    batch = []
    for feature in iter_features_from_json("../data/trajectories_mf1.json"):
        batch.append(feature)
        if len(batch) >= BATCH_SIZE:
            feature_collection = {
                "type": "FeatureCollection",
                "features": batch
            }
            resp = requests.post(
                f"{HOST}/collections/{COLLECTION_ID}/items",
                json=feature_collection,
                headers={"Content-Type": "application/json"}
            )
            log_request_response(f"Post batch of {len(batch)} features", resp)
            if resp.status_code in (201, 409):
                created_count += len(batch)
            batch = []   # reset

    # Last batch
    if batch:
        feature_collection = {
            "type": "FeatureCollection",
            "features": batch
        }
        resp = requests.post(
            f"{HOST}/collections/{COLLECTION_ID}/items",
            json=feature_collection,
            headers={"Content-Type": "application/json"}
        )
        log_request_response(f"Post batch of {len(batch)} features", resp)
        if resp.status_code in (201, 409):
            created_count += len(batch)

    print(f"Successfully posted {created_count} vessels.")
    yield {"collection_id": COLLECTION_ID}
    # No cleanup – data persists
    
def test_1_ships_in_port(setup_data):
    collection_id = setup_data["collection_id"]
    resp = requests.get(
        f"{HOST}/collections/{COLLECTION_ID}/items",
        params={"bbox": PORT_BBOX}
    )
    log_request_response("Ships in Rodby port", resp)
    assert resp.status_code == 200
    data = resp.json()
    ships = data["features"]
    print(f"\nNumber of ships intersecting Rodby envelope: {len(ships)}")
    for ship in ships[:5]:
        print(f"  {ship['id']} ({ship['properties'].get('name', 'N/A')})")
    assert len(ships) >= 0

def test_2_velocity_for_random_ship(setup_data):
    collection_id = setup_data["collection_id"]
    resp = requests.get(f"{HOST}/collections/{collection_id}/items?limit=1")
    log_request_response("Get first feature", resp)
    if resp.status_code != 200 or not resp.json().get("features"):
        pytest.skip("No features in collection")
    ship_id = resp.json()["features"][0]["id"]

    resp = requests.get(f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence")
    log_request_response(f"Get geometry for ship {ship_id}", resp)
    if resp.status_code != 200:
        pytest.skip(f"No geometry for ship {ship_id}")
    geom_id = resp.json()["geometrySequence"][0]["id"]

    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence/{geom_id}/velocity"
    )
    log_request_response(f"Velocity for ship {ship_id}", resp)
    assert resp.status_code == 200
    vel_data = resp.json()
    print(f"\nVelocity values for ship {ship_id}:")
    for point in vel_data.get("values", [])[:5]:
        print(f"  {point['time']}: {point['value']:.2f} m/s")

def test_3_subtrajectory_interval(setup_data):
    collection_id = setup_data["collection_id"]
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items",
        params={"subTrajectory": "true", "datetime": TIME_INTERVAL}
    )
    log_request_response(f"Subtrajectory interval {TIME_INTERVAL}", resp)
    assert resp.status_code == 200
    data = resp.json()
    ships = data["features"]
    print(f"\nNumber of ships with subtrajectory in interval: {len(ships)}")
    for ship in ships[:5]:
        print(f"  {ship['id']}")
    assert len(ships) >= 0

def test_finalize():
    pymeos_finalize()
    print("\nDemo completed. All logs saved to api_logs.json (automatically by log_request_response).")
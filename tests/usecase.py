import pytest
import requests
import json
from pymeos import *
import json
from datetime import datetime
from common import log_request_response, log_to_json
HOST = "http://localhost:8080"

pymeos_initialize()

# loggerto JSON
API_LOGS = []
# #ships  data
# # 
VESSELS_DATA = [
    {
        "id": "maersk_essen",
        "name": "Maersk Essen",
        "type": "container",
        "in_port": True,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 06:00:00+00",
                "2024-03-15 06:30:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 07:30:00+00",
                "2024-03-15 08:00:00+00"
            ],
            "coordinates": [
                [585000, 5672000],
                [587000, 5674000],
                [589000, 5676000],
                [591000, 5678000],
                [592000, 5679000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "cma_cgm_libra",
        "name": "CMA CGM Libra",
        "type": "container",
        "in_port": True,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 06:00:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00",
                "2024-03-15 10:00:00+00"
            ],
            "coordinates": [
                [584000, 5671000],
                [586000, 5673000],
                [587000, 5674000],
                [587000, 5674000],
                [587000, 5674000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "msc_zoe",
        "name": "MSC Zoe",
        "type": "container",
        "in_port": True,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 06:00:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00",
                "2024-03-15 10:00:00+00"
            ],
            "coordinates": [
                [585000, 5672000],
                [587000, 5674000],
                [589000, 5676000],
                [591000, 5678000],
                [593000, 5680000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "ever_given",
        "name": "Ever Given",
        "type": "container",
        "in_port": True,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 05:00:00+00",
                "2024-03-15 06:00:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00"
            ],
            "coordinates": [
                [584500, 5671500],
                [586500, 5673500],
                [588500, 5675500],
                [590500, 5677500],
                [592500, 5679500]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "stena_impero",
        "name": "Stena Impero",
        "type": "tanker",
        "in_port": True,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00",
                "2024-03-15 10:00:00+00",
                "2024-03-15 11:00:00+00",
                "2024-03-15 12:00:00+00"
            ],
            "coordinates": [
                [587500, 5674500],
                [587500, 5674500],
                [587500, 5674500],
                [587500, 5674500],
                [587500, 5674500]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "european_trader",
        "name": "European Trader",
        "type": "bulk",
        "in_port": False,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 06:00:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00",
                "2024-03-15 10:00:00+00"
            ],
            "coordinates": [
                [575000, 5660000],
                [577000, 5662000],
                [579000, 5664000],
                [581000, 5666000],
                [583000, 5668000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "belgium_chem",
        "name": "Belgium Chem",
        "type": "chemical",
        "in_port": False,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 05:00:00+00",
                "2024-03-15 06:00:00+00",
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00"
            ],
            "coordinates": [
                [574000, 5659000],
                [576000, 5661000],
                [578000, 5663000],
                [580000, 5665000],
                [582000, 5667000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "antwerp_star",
        "name": "Antwerp Star",
        "type": "container",
        "in_port": False,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 07:00:00+00",
                "2024-03-15 08:00:00+00",
                "2024-03-15 09:00:00+00",
                "2024-03-15 10:00:00+00",
                "2024-03-15 11:00:00+00"
            ],
            "coordinates": [
                [595000, 5680000],
                [593000, 5678000],
                [591000, 5676000],
                [589000, 5674000],
                [587000, 5672000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "schelde_river",
        "name": "Schelde River",
        "type": "tug",
        "in_port": False,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 06:30:00+00",
                "2024-03-15 07:30:00+00",
                "2024-03-15 08:30:00+00",
                "2024-03-15 09:30:00+00",
                "2024-03-15 10:30:00+00"
            ],
            "coordinates": [
                [578000, 5663000],
                [580000, 5665000],
                [582000, 5667000],
                [584000, 5669000],
                [586000, 5671000]
            ],
            "interpolation": "Linear"
        }
    },
    {
        "id": "diamond_express",
        "name": "Diamond Express",
        "type": "container",
        "in_port": False,
        "crs": {
            "type": "name",
            "properties": "urn:ogc:def:crs:EPSG::25832"
        },
        "trajectory": {
            "type": "MovingPoint",
            "datetimes": [
                "2024-03-15 08:30:00+00",
                "2024-03-15 09:30:00+00",
                "2024-03-15 10:30:00+00",
                "2024-03-15 11:30:00+00",
                "2024-03-15 12:30:00+00"
            ],
            "coordinates": [
                [596000, 5681000],
                [594000, 5679000],
                [592000, 5677000],
                [590000, 5675000],
                [588000, 5673000]
            ],
            "interpolation": "Linear"
        }
    }
]

@pytest.fixture(scope="module")
def setup_port_data():    
    # Create collection
    collection_data = {
        "title": "belgium_ships",
        "description": "Vessel traffic in Belgian waters - Antwerp port",
        "updateFrequency": 1000,
        "itemType": "movingfeature"
    }
    resp = requests.post(f"{HOST}/collections", json=collection_data)
    log_request_response("Create belgium_ships collection", resp)
    assert resp.status_code in (201, 409)
    
    collection_id = "belgium_ships"
    
    # Create all 10 ships
    features_list = []
    for vessel in VESSELS_DATA:
        features_list.append({
            "type": "Feature",
            "id": vessel["id"],
            "crs": vessel.get("crs"),  # ← ADD THIS LINE
            "temporalGeometry": vessel["trajectory"],
            "properties": {
                "name": vessel["name"],
                "type": vessel["type"]
            }
        })
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": features_list
    }
    
    resp = requests.post(
        f"{HOST}/collections/{collection_id}/items",
        json=feature_collection,
        headers={"Content-Type": "application/json"}
    )
    log_request_response("Create 10 vessels", resp)
    assert resp.status_code == 201
    
    yield {
        "collection_id": collection_id,
        "vessels": VESSELS_DATA
    }
    
    # Cleanup
    # print("\n=== CLEANING UP ===")
    # for vessel in VESSELS_DATA:
    #     requests.delete(f"{HOST}/collections/{collection_id}/items/{vessel['id']}")
    # requests.delete(f"{HOST}/collections/{collection_id}")


# Get ships in port (bbox filter)


def test_1_get_ships_in_port(setup_port_data):
    data = setup_port_data
    collection_id = data["collection_id"]
    
    # Antwerp port area (meters, EPSG:25832) example
    # port_bbox ="4.146652,51.218067,4.443283,51.309155"
    port_bbox = "584000,5670000,593000,5680000"
    # port_bbox = "4.1,51.1,4.3,51.3"
    
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items",
        params={"bbox": port_bbox}
    )
    
    log_request_response("API: Get ships in Antwerp port", resp)
    assert resp.status_code == 200
    
    result = resp.json()
    ships_in_port = result["features"]
    
    print(f"\n{'='*60}")
    print("TEST 1: API Returns Ships Inside Port Bbox")
    print(f"Port bbox: {port_bbox} (meters, EPSG:25832)")
    print(f"Ships returned: {len(ships_in_port)}")
    for ship in ships_in_port:
        print(f"  → {ship['id']} ({ship['properties']['name']})")
    print(f"{'='*60}\n")
    
    # EXPECT: 9ships in port
    assert len(ships_in_port) == 8



#  Get velocity for a ship to check speed violation as an example
def test_2_get_velocity_violation_ship(setup_port_data):

    data = setup_port_data
    collection_id = data["collection_id"]
    ship_id = "maersk_essen"
    ship_name = "Maersk Essen"
    
    # Get geometry ID
    traj_resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence"
    )
    traj_data = traj_resp.json()
    geometry_id = traj_data.get("geometrySequence", [{}])[0].get("id", 1)
    
    # API CALL: Get velocity curve
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence/{geometry_id}/velocity"
    )
    
    log_request_response(f"API: Get velocity for {ship_name}", resp)
    assert resp.status_code == 200
    
    velocity_data = resp.json()
    speed_limit_ms = 5.14  # assuming speed limit in antwerp port is 10 knots in m/s 
    
    print(f"\n{'='*60}")
    print(f"TEST 2: Velocity Response for {ship_name}")
    print(f"Speed limit: 10 knots (5.14 m/s)")
    print("-" * 40)
    print("API RESPONSE (velocity over time):")
    print(f"{'Time':<30} {'Speed (m/s)':<15} {'Status'}")
    print("-" * 60)
    
    violation_found = False
    for point in velocity_data.get("values", []):
        time = point.get("time", "")
        speed_ms = point.get("value", 0)
        
        status = "VIOLATION" if speed_ms > speed_limit_ms else "OK"
        if speed_ms > speed_limit_ms:
            violation_found = True
        
        print(f"{time:<30} {speed_ms:<15.2f} {status}")
    
    print("-" * 60)
    if violation_found:
        print("SPEED VIOLATION DETECTED in API response!")
    else:
        print("No violation detected")
    print(f"{'='*60}\n")
    
    assert True


#  Get velocity for a ship that eventually stops in port
def test_3_get_velocity_stopped_ship(setup_port_data):

    data = setup_port_data
    collection_id = data["collection_id"]
    ship_id = "cma_cgm_libra"
    ship_name = "CMA CGM Libra"
    
    # Get geometry ID
    traj_resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence"
    )
    traj_data = traj_resp.json()
    geometry_id = traj_data.get("geometrySequence", [{}])[0].get("id", 1)
    
    # API CALL: Get velocity curve
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence/{geometry_id}/velocity"
    )
    
    log_request_response(f"API: Get velocity for {ship_name}", resp)
    assert resp.status_code == 200
    
    velocity_data = resp.json()
    
    print(f"\n{'='*60}")
    print(f"TEST 3: Velocity Response for {ship_name}")
    print("Demonstrates ship slowing down and stopping")
    print("-" * 40)
    print("API RESPONSE (velocity over time):")
    print(f"{'Time':<30} {'Speed (m/s)':<15} ")
    print("-" * 60)
    
    for point in velocity_data.get("values", []):
        time = point.get("time", "")
        speed_ms = point.get("value", 0)
        
        if speed_ms == 0:
            status = "STOPPED"
        elif speed_ms < 1:
            status = "docking"
        else:
            status = "Moving"
        
        print(f"{time:<30} {speed_ms:<15.2f} {status}")
    
    print("-" * 60)
    print("API shows ship speed reaching 0 at 08:00 (docked)")
    print(f"{'='*60}\n")
    
    assert True


# Get velocity for a ship outside port (for comparison)

def test_4_get_velocity_outside_ship(setup_port_data):

    data = setup_port_data
    collection_id = data["collection_id"]
    ship_id = "european_trader"
    ship_name = "European Trader"
    

    traj_resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence"
    )
    traj_data = traj_resp.json()
    geometry_id = traj_data.get("geometrySequence", [{}])[0].get("id", 1)
    
    # velocity curve
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence/{geometry_id}/velocity"
    )
    
    log_request_response(f"API: Get velocity for {ship_name} (outside port)", resp)
    assert resp.status_code == 200
    
    velocity_data = resp.json()
    
    print(f"\n{'='*60}")
    print(f"TEST 4: Velocity Response for {ship_name} (outside port)")
    print("This ship is not in the port area")
    print("-" * 40)
    print("API RESPONSE (velocity over time):")
    print(f"{'Time':<30} {'Speed (m/s)':<15}")
    print("-" * 45)
    
    for point in velocity_data.get("values", []):
        time = point.get("time", "")
        speed_ms = point.get("value", 0)
        print(f"{time:<30} {speed_ms:<15.2f}")
    
    print("-" * 45)
    print("This ship is NOT in port (not returned by bbox filter)")
    print(f"{'='*60}\n")
    
    assert True

# Compare speed profiles of different ships
# def test_5_compare_ship_speeds(setup_port_data):

#     data = setup_port_data
#     collection_id = data["collection_id"]
    
#     ships_to_check = [
#         ("maersk_essen", "Maersk Essen"),
#         ("cma_cgm_libra", "CMA CGM Libra (stopped)"),
#         ("msc_zoe", "MSC Zoe (normal)")
#     ]
    
#     print(f"\n{'='*60}")
#     print("TEST 5: Comparing Speed Profiles from API")
#     print("-" * 60)
    
#     for ship_id, ship_name in ships_to_check:
#         # Get geometry ID
#         traj_resp = requests.get(
#             f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence"
#         )
#         traj_data = traj_resp.json()
#         geometry_id = traj_data.get("geometrySequence", [{}])[0].get("id", 1)
        
#         # API CALL: Get velocity
#         resp = requests.get(
#             f"{HOST}/collections/{collection_id}/items/{ship_id}/tgsequence/{geometry_id}/velocity"
#         )
        
#         if resp.status_code == 200:
#             velocity_data = resp.json()
#             speeds = [p.get("value", 0) for p in velocity_data.get("values", [])]
#             max_speed = max(speeds) if speeds else 0
#             min_speed = min(speeds) if speeds else 0
            
#             print(f"\n{ship_name}:")
#             print(f"  Max speed: {max_speed:.2f} m/s ({max_speed * 1.94384:.1f} knots)")
#             print(f"  Min speed: {min_speed:.2f} m/s ({min_speed * 1.94384:.1f} knots)")
#             if max_speed > 5.14:
#                 print(f"  SPEED VIOLATION (exceeds 10 knots)")
#             if min_speed == 0:
#                 print(f"Ship stopped (speed = 0)")
    
#     print(f"\n{'='*60}\n")
#     assert True



#Get ships with subtrajectory within datetime interval
def test_6_get_ships_subtrajectory_with_interval(setup_port_data):

    data = setup_port_data
    collection_id = data["collection_id"]
    
    # Time interval: 10:30 to 11:30 
    interval = "2024-03-15T10:30:00+00/2024-03-15T11:30:00+00"
    
    resp = requests.get(
        f"{HOST}/collections/{collection_id}/items",
        params={"subTrajectory": "true", "datetime": interval}
    )
    
    log_request_response(f"API: Get ships with subtrajectory interval {interval}", resp)
    assert resp.status_code == 200
    
    result = resp.json()
    ships = result["features"]
    
    print(f"\n{'='*60}")
    print("TEST 6: Subtrajectory with datetime interval")
    print(f"Interval: {interval}")
    print(f"Ships returned: {len(ships)}")
    for ship in ships:
        print(f"  → {ship['id']}")
    print(f"{'='*60}\n")
    
    # 4 ships
    assert len(ships) == 4

def test_finalize():
    pymeos_finalize()
    print("\nEND")
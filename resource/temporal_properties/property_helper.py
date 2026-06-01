from datetime import datetime
import json

# some code refactoring to use these is preferable check clean not urgent
def build_property_response(prop, base_url, path):
    return {
        "name": prop["property_name"],
        "type": prop["property_type"],
        "form": prop.get("form"),
        "description": prop.get("description"),
        "links": [
            {
                "href": f"{base_url}{path}",
                "rel": "self",
                "type": "application/json"
            }
        ]
    }


def build_properties_list_response(properties, base_url, path):
    return {
        "temporalProperties": properties,
        "links": [
            {
                "href": f"{base_url}{path}",
                "rel": "self",
                "type": "application/json"
            }
        ],
        "timeStamp": datetime.utcnow().isoformat() + "Z",
        "numberMatched": len(properties),
        "numberReturned": len(properties)
    }

def build_property_values_response(property_data, values, base_url, path):
    return {
        "name": property_data["property_name"],
        "type": property_data["property_type"],
        "form": property_data.get("form"),
        "description": property_data.get("description"),
        "values": values,
        "links": [
            {
                "href": f"{base_url}{path}",
                "rel": "self",
                "type": "application/json"
            }
        ]
    }

def validate_property_type(prop_type):
    valid_types = ["TBoolean", "TText", "TInteger", "TReal", "TImage"]
    return prop_type in valid_types

#interpolation type:
def validate_interpolation(interpolation):
    valid_interpolations = ["Discrete", "Step", "Linear", "Regression"]
    return interpolation in valid_interpolations
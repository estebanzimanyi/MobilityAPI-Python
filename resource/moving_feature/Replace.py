# PUT /collections/{collectionId}/items/{mFeatureId}
# Replace a moving feature: its temporal geometry and properties are replaced by
# the posted Feature. The feature is deleted (the FK cascade removes its temporal
# geometries / properties / values) and re-inserted under the same id, in one
# transaction, so the replace reuses the create path and the extent trigger.
import json

from utils import send_json_response
from resource.moving_features.Create import insert_feature


def put_single_moving_feature(self, collection_id, feature_id, connection, cursor):
    try:
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length else {}

        cursor.execute("SELECT id FROM collections WHERE id = %s", (collection_id,))
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return

        cursor.execute(
            "SELECT id FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id),
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Feature '{feature_id}' not found in collection '{collection_id}'")
            return

        # Full replace: drop the feature (cascades to its temporal geometries,
        # properties and values) and re-insert it under the path id.
        cursor.execute(
            "DELETE FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id),
        )
        body["id"] = feature_id
        if body.get("type") is None:
            body["type"] = "Feature"
        insert_feature(self, body, collection_id, connection, cursor)
        connection.commit()

        send_json_response(self, 200, {"message": "replaced", "id": feature_id})

    except Exception as e:
        connection.rollback()
        self.handle_error(400, f"Replace failed: {str(e)}")

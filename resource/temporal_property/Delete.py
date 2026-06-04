# REQ43: /req/movingfeatures/tproperty-delete
# REQ 46: /req/movingfeatures/tproperty-delete-success

from utils import send_json_response
import traceback

#  DELETE /collections/{collectionId}/items/{featureId}/tproperties/{propertyName}
def delete_temporal_property(self, collection_id, feature_id, property_name, connection, cursor):
    try:
        #collection and feature existance chacks::::::::::::::::::::::
        cursor.execute(
            "SELECT id FROM collections WHERE id = %s",
            (collection_id,)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
         
        cursor.execute(
            "SELECT id FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Feature '{feature_id}' not found in collection '{collection_id}'")
            return
        #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        # delete by porperty name and featid -->on delete cascades temporal_values
        cursor.execute("""
            DELETE FROM temporal_properties
            WHERE feature_id = %s AND property_name = %s
            RETURNING id
        """, (feature_id, property_name))
        
        deleted = cursor.fetchone()
        if not deleted:
            self.handle_error(404, f"Property '{property_name}' not found for feature '{feature_id}'")
            return
        
        connection.commit()
        
        # 204 
        self.send_response(204)
        self.end_headers()
        
    except Exception as e:
        connection.rollback()
        # print(f"Error delete_temporal property: {e}")
        # traceback.print_exc()
        self.handle_error(500, f"Internal server error: {str(e)}")
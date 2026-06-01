# REQ 48: /req/movingfeatures/tpvalue-delete
# REQ 49: /req/movingfeatures/tpvalue-delete-success

from utils import send_json_response
import traceback

# DELETE /collecstions/{collectionId}/items/{featureId}/tproperties/{propertyName}/{valueId}
def delete_temporal_primitive_value(self, collection_id, feature_id, property_name, value_id, connection, cursor):

    try:
        # collection exists
        cursor.execute(
            "SELECT id FROM collections WHERE id = %s",
            (collection_id,)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        
        # feature exists
        cursor.execute(
            "SELECT id FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Feature '{feature_id}' not found in collection '{collection_id}'")
            return
        
        # Get property id:
        cursor.execute("""
            SELECT id FROM temporal_properties
            WHERE feature_id = %s AND property_name = %s
        """, (feature_id, property_name))
        prop_row = cursor.fetchone()
        if prop_row is None:
            self.handle_error(404, f"Property '{property_name}' not found for feature '{feature_id}'")
            return
        property_id = prop_row[0]
        
        #DELETE FROM temporal_values for the property
        cursor.execute("""
            DELETE FROM temporal_values
            WHERE id = %s AND property_id = %s
            RETURNING id
        """, (value_id, property_id))
        
        deleted = cursor.fetchone()
        if not deleted:
            self.handle_error(404, f"Value '{value_id}' not found for property '{property_name}'")
            return
        
        connection.commit()
        
        #204 delete success
        self.send_response(204)
        self.end_headers()
    except Exception as e:
        connection.rollback()
        # print(f"Error in delete TemporalPrimitiveValue: {e}")
        # traceback.print_exc()
        self.handle_error(500, f"Internal server error: {str(e)}")
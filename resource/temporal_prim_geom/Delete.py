# REQ 30: /req/movingfeatures/tpgeometry-delete
# REQ 31: /req/movingfeatures/tpgeometry-delete-success

from utils import send_json_response


# DELETE base/collections/{collectionId}/items/{featureId}/tgsequence/{geometryId}
def delete_single_temporal_primitive_geo(self, collection_id, feature_id, geometry_id, connection, cursor):
    
    try:
        #---------------------------------collection && feature && geomerty exist ??---------------------------------------
        cursor.execute(
            "SELECT id FROM collections WHERE id = %s",
            (collection_id,)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Collection '{collection_id}' not found")
            return
        #feature exists?
        # addition 14/03 clean
        cursor.execute(
            "SELECT id FROM moving_features WHERE id = %s AND collection_id = %s",
            (feature_id, collection_id)
        )
        if cursor.fetchone() is None:
            self.handle_error(404, f"Feature '{feature_id}' not found")
            return
        # {geometry_id} is the 1-based index of a member sequence of the trajectory
        try:
            member = int(geometry_id)
        except (TypeError, ValueError):
            self.handle_error(400, "invalid temporal geometry id (1-based index into the sequence)")
            return
        cursor.execute(
            "SELECT numSequences(trajectory) FROM temporal_geometries WHERE feature_id = %s AND collection_id = %s",
            (feature_id, collection_id),
        )
        row = cursor.fetchone()
        if row is None or row[0] is None:
            self.handle_error(404, f"Temporal geometry {geometry_id} not found")
            return
        nseq = row[0]
        if member < 1 or member > nseq:
            self.handle_error(404, f"Temporal geometry {geometry_id} not found")
            return
        if nseq == 1:
            self.handle_error(409, "the feature has a single temporal geometry; delete the feature to remove it")
            return
        #----------------------------------------------------------------------------------------------------------------------
        # Remove the member sequence by rebuilding the sequence set from the kept
        # members. deleteTime is not used here: its gap-fill semantics reconnect
        # the surviving fragments into a single sequence, whereas deleting a
        # temporal primitive geometry must leave the other members distinct.
        cursor.execute(
            """UPDATE temporal_geometries SET trajectory = (
                   SELECT merge(seq)
                   FROM unnest(sequences(trajectory)) WITH ORDINALITY AS u(seq, ord)
                   WHERE ord <> %s
               )
               WHERE feature_id = %s AND collection_id = %s
            """, (member, feature_id, collection_id)
        )

        connection.commit()
        
        # response Req 31)
        self.send_response(204)
        self.end_headers()
        
    except Exception as e:
        connection.rollback()
        print(f"Error in delete_single_temporal_primitive_geo: {e}", flush=True)
        self.handle_error(500, f"Internal server error: {str(e)}")
# REQ 32: /req/movingfeatures/tpgeometry-query
# REQ 33: /req/movingfeatures/tpgeometry-query-success
# SECTION 8.7.5. Acceleration Query
from utils import send_json_response


# GET /collections/{collectionId}/items/{featureId}/tgsequence/{geometryId}/acceleration
def get_acceleration(self, collection_id, feature_id, geometry_id, connection, cursor):
    # Acceleration is not derivable for this motion model: with linearly
    # interpolated position the speed is piecewise-constant (Step), so its
    # derivative is zero within each segment and undefined at the vertices. The
    # value is not approximated (no finite difference, no coercion of the speed
    # to Linear) — the same contract as the Go tier, which returns 501 here.
    self.handle_error(
        501,
        "acceleration is not derivable: linearly interpolated position gives a "
        "piecewise-constant (Step) speed, whose derivative is zero within each "
        "segment and undefined at the vertices",
    )

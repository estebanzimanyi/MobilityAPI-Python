"""Unit tests for the bulk-ingest parsing and decompression, with no server or
database: the SQL append path is exercised by the integration suite and shares
MobilityDB's appendInstant with the rest of the tier.
"""
import gzip
import io
import zlib

import pyarrow as pa
import pyarrow.parquet as pq

from resource.bulk.bulk_helper import (
    decompress, parse_geojson_points, parse_geoparquet, _instant)

GEOJSON = (
    b'{"type":"FeatureCollection","features":['
    b'{"type":"Feature","id":"bus_42","geometry":{"type":"Point","coordinates":[4.3517,50.8466]},'
    b'"properties":{"datetime":"2026-02-26T10:00:00Z"}},'
    b'{"type":"Feature","geometry":{"type":"Point","coordinates":[4.349,50.8501]},'
    b'"properties":{"id":"bus_57","time":"2026-02-26T10:00:00Z"}}]}'
)


def test_decompress_gzip_deflate_identity():
    assert decompress(GEOJSON, None) == GEOJSON
    assert decompress(GEOJSON, "identity") == GEOJSON
    assert decompress(gzip.compress(GEOJSON), "gzip") == GEOJSON
    assert decompress(zlib.compress(GEOJSON), "deflate") == GEOJSON
    # raw (headerless) deflate is accepted via the fallback
    co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    raw = co.compress(GEOJSON) + co.flush()
    assert decompress(raw, "deflate") == GEOJSON


def test_decompress_unsupported():
    try:
        decompress(GEOJSON, "lzma")
    except ValueError:
        return
    raise AssertionError("unsupported Content-Encoding should raise ValueError")


def test_parse_geojson_points():
    obs, srid = parse_geojson_points(GEOJSON)
    assert srid == 4326
    assert len(obs) == 2
    assert obs[0] == {"id": "bus_42", "x": 4.3517, "y": 50.8466, "t": "2026-02-26T10:00:00Z"}
    assert obs[1]["id"] == "bus_57"  # id and time taken from properties


def test_parse_geoparquet():
    table = pa.table({
        "geometry": pa.array([b"\x01\x02\x03", b"\x04\x05\x06"], type=pa.binary()),
        "id": ["bus_42", "bus_57"],
        "ts": ["2026-02-26T10:00:00Z", "2026-02-26T10:01:00Z"],
    })
    buf = io.BytesIO()
    pq.write_table(table, buf)
    obs, srid = parse_geoparquet(buf.getvalue())
    assert srid == 4326
    assert len(obs) == 2
    assert obs[0]["id"] == "bus_42" and obs[0]["wkb"] == b"\x01\x02\x03"
    assert obs[1]["t"] == "2026-02-26T10:01:00Z"


def test_instant_sql_fragment():
    xy, args = _instant({"x": 4.35, "y": 50.84, "t": "2026-02-26T10:00:00Z"}, 4326)
    assert "ST_MakePoint" in xy and args == (4.35, 50.84, 4326, "2026-02-26T10:00:00Z")
    wkb, wargs = _instant({"wkb": b"\x01", "t": "2026-02-26T10:00:00Z"}, 4326)
    assert "ST_GeomFromWKB" in wkb and wargs == (b"\x01", 4326, "2026-02-26T10:00:00Z")

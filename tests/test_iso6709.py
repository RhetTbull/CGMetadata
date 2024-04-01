"""Test ISO 6709 functions"""

import pytest

from cgmetadata.iso6709 import parse_iso_6709

TEST_DATA = {
    "Atlantic Ocean": ["+00-025/", (0.0, -25.0, None, None)],
    "France": ["+46+002/", (46.0, 2.0, None, None)],
    "Paris": ["+48.52+002.20/", (48.52, 2.2, None, None)],
    "Eiffel Tower": ["+48.8577+002.295", (48.8577, 2.295, None, None)],
    "Mount Everest": [
        "+27.5916+086.5640+8850CRSWGS_84/",
        (27.5916, 86.564, 8850.0, "WGS_84"),
    ],
    "North Pole": ["+90+000/", (90.0, 0.0, None, None)],
    "Pacific Ocean": ["+00-160/", (0.0, -160.0, None, None)],
    "South Pole": ["-90+000+2800CRSWGS_84/", (-90.0, 0.0, 2800.0, "WGS_84")],
    "South Pole with URL": [
        "-90+000+2800CRShttps://test.org/",
        (-90.0, 0.0, 2800.0, "https://test.org"),
    ],
    "South Pole no terminator": [
        "-90+000+2800CRSWGS_84",
        (-90.0, 0.0, 2800.0, "WGS_84"),
    ],
    "South Pole (no CRS)": [
        "-90+000+2800/",
        (-90.0, 0.0, 2800.0, None),
    ],  # not spec compliant but Apple does this
    "United States": ["+38-097/", (38.0, -97.0, None, None)],
    "New York City": ["+40.75-074.00/", (40.75, -74.0, None, None)],
    "Statue of Liberty": ["+40.6894-074.0447/", (40.6894, -74.0447, None, None)],
}

INVALID_DATA = ["+90+2800CRSWGS_84", "+90", "+90+45+45+45", "FooBar"]


@pytest.mark.parametrize("iso_6709_str, expected", TEST_DATA.values())
def test_parse_iso_6709(iso_6709_str, expected):
    """Test parse_iso_6709 function"""
    assert parse_iso_6709(iso_6709_str) == expected


@pytest.mark.parametrize("iso_6709_str", INVALID_DATA)
def test_parse_iso_6709_invalid(iso_6709_str):
    """Test parse_iso_6709 function with invalid data"""
    with pytest.raises(ValueError):
        parse_iso_6709(iso_6709_str)

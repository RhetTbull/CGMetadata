"""Test ImageMetadata class"""

from __future__ import annotations

import pytest

from cgmetadata import EXIF, GPS, IPTC, TIFF, WEBP, XMP, ImageMetadata

TEST_JPG = "tests/data/test.jpeg"
TEST_PNG = "tests/data/test.png"
TEST_TIFF = "tests/data/test.tiff"
TEST_RAW = "tests/data/test.cr2"

TEST_IMAGES = [TEST_JPG, TEST_PNG, TEST_TIFF, TEST_RAW]

TEST_JPG_XMP = "tests/data/test.jpeg.xmp"
TEST_JPG_MODIFIED_XMP = "tests/data/modified.xmp"


def test_imagemetadata_asdict():
    """Test ImageMetadata().asdict()"""
    md = ImageMetadata(TEST_JPG)
    md_dict = md.asdict()
    assert md_dict.get(XMP, {}) == md.xmp
    assert md_dict.get(EXIF, {}) == md.exif
    assert md_dict.get(IPTC, {}) == md.iptc
    assert md_dict.get(TIFF, {}) == md.tiff
    assert md_dict.get(GPS, {}) == md.gps


def test_imagemetdata_xmp():
    """Test ImageMetadata().xmp"""
    md = ImageMetadata(TEST_JPG)
    assert sorted(md.xmp["dc:subject"]) == ["fruit", "tree"]


def test_imagemetadata_exif():
    """Test ImageMetadata().exif"""
    md = ImageMetadata(TEST_JPG)
    assert md.exif["LensMake"] == "Apple"


def test_imagemetadata_tiff():
    """Test ImageMetadata().tiff"""
    md = ImageMetadata(TEST_JPG)
    assert md.tiff["Make"] == "Apple"


def test_imagemetadata_iptc():
    """Test ImageMetadata().iptc"""
    md = ImageMetadata(TEST_JPG)
    assert md.iptc["Keywords"] == ["fruit", "tree"]


def test_imagemetadata_gps():
    """Test ImageMetadata().gps"""
    md = ImageMetadata(TEST_JPG)
    assert md.gps["LatitudeRef"] == "N"


@pytest.mark.parametrize("filepath", TEST_IMAGES)
def test_imagemetadata_filetypes(filepath):
    """Test ImageMetadata() with different filetypes"""
    md = ImageMetadata(filepath)
    assert md.xmp["dc:description"]

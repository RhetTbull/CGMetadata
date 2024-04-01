"""Test ImageMetadata class"""

from __future__ import annotations

import pytest

from cgmetadata import VideoMetadata, XMP

TEST_MOV = "tests/data/test.MOV"

TEST_MOV_XMP = "tests/data/test.MOV.xmp"


def test_videometadata_asdict():
    """Test ImageMetadata().asdict()"""
    md = VideoMetadata(TEST_MOV)
    md_dict = md.asdict()
    assert md_dict.get(XMP, {}) == md.xmp


def test_imagemetdata_xmp():
    """Test ImageMetadata().xmp"""
    md = VideoMetadata(TEST_MOV)
    assert sorted(md.xmp["dc:subject"]) == ["Coffee", "Espresso"]

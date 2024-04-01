"""Test ImageMetadata class"""

from __future__ import annotations

import pytest

from cgmetadata import XMP, VideoMetadata
from cgmetadata.xmp import metadata_dictionary_from_xmp_packet

TEST_MOV = "tests/data/test.MOV"

TEST_MOV_XMP = "tests/data/test.MOV.xmp"


def test_videometadata_asdict():
    """Test VideoMetadata().asdict()"""
    md = VideoMetadata(TEST_MOV)
    md_dict = md.asdict()
    assert md_dict.get(XMP, {}) == md.xmp


def test_videometadata_xmp():
    """Test VideoMetadata().xmp"""
    md = VideoMetadata(TEST_MOV)
    assert sorted(md.xmp["dc:subject"]) == ["Coffee", "Espresso"]


def test_videometadata_xmp_dumps():
    """Test VideoMetadata().xmp_dumps()"""
    md = VideoMetadata(TEST_MOV)
    assert md.xmp_dumps() == open(TEST_MOV_XMP).read()
    xmp = metadata_dictionary_from_xmp_packet(md.xmp_dumps())
    assert sorted(xmp["dc:subject"]) == ["Coffee", "Espresso"]


def test_videometadata_xmp_dump(tmp_path):
    """Test VideoMetadata().xmp_dump()"""
    md = VideoMetadata(TEST_MOV)
    xmp_file = tmp_path / "test.MOV.xmp"
    with open(xmp_file, "wb") as f:
        md.xmp_dump(f)
    with open(TEST_MOV_XMP) as expected:
        assert xmp_file.read_text() == expected.read()

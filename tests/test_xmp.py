"""Test XMP functions"""

from cgmetadata.xmp import is_xmp_packet, metadata_dictionary_from_xmp_packet

XMP_FILE = "tests/data/test.jpeg.xmp"

NOT_XMP = "FooBar"


def test_is_xmp_packet():
    """Test is_xmp_packet"""
    xmp_packet = open(XMP_FILE).read()
    assert is_xmp_packet(xmp_packet)


def test_is_xmp_packet_not_xmp():
    """Test is_xmp_packet with non-XMP"""
    assert not is_xmp_packet(NOT_XMP)


def test_metadata_dictionary_from_xmp_packet():
    """Test metadata_dictionary_from_xmp_packet"""
    xmp_packet = open(XMP_FILE).read()
    xmp_dict = metadata_dictionary_from_xmp_packet(xmp_packet)
    assert sorted(xmp_dict["dc:subject"]) == ["fruit", "tree"]

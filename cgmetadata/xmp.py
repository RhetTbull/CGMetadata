"""Utilities for working with XMP data"""

from __future__ import annotations

from typing import Any

import objc
import Quartz
from Foundation import NSData, __NSCFData

from .constants import XMP_PACKET_FOOTER, XMP_PACKET_HEADER
from .metadata import MetadataError, metadata_dictionary_from_image_metadata_ref
from .utils import single_quotes_to_double_quotes, strip_xmp_packet


def is_xmp_packet(value: bytes | str | __NSCFData) -> bool:
    """Check if a metadata value is an XMP packet.

    Args:
        value: A metadata value.

    Returns: True if the value is an XMP packet, False otherwise.
    """
    if isinstance(value, (bytes, __NSCFData)):
        value = value.decode("utf-8")
    return value.startswith("<?xpacket begin='\ufeff") or value.startswith(
        '<?xpacket begin="\ufeff'
    )


def metadata_dictionary_from_xmp_packet(
    xmp: str | bytes | __NSCFData,
) -> dict[str, Any]:
    """Extract key-value pairs from an XMP packet.

    Args:
        xmp: str or bytes for XMP packet

    Returns: dict with key/value pairs from the XMP packet.

    Raises:
        ValueError: if XMP packet cannot be decoded.
    """
    with objc.autorelease_pool():
        if isinstance(xmp, (bytes, __NSCFData)):
            xmp = xmp.decode("utf-8")
        xmp = single_quotes_to_double_quotes(xmp)
        xmp = strip_xmp_packet(xmp)
        xmp = xmp.encode("utf-8")
        if mdref := metadata_ref_create_from_xmp(xmp):
            return metadata_dictionary_from_image_metadata_ref(mdref)
        raise ValueError("Failed to create metadata ref from XMP packet")


def metadata_ref_serialize_xmp(metadata_ref: Quartz.CGImageMetadataRef) -> bytes:
    """Create serialized XMP from a Quartz.CGImageMetadataRef."""
    with objc.autorelease_pool():
        data = Quartz.CGImageMetadataCreateXMPData(metadata_ref, None)
        if not data:
            return b""
        xmp = bytes(data)
        del data
        return xmp


def metadata_ref_create_from_xmp(xmp: bytes) -> Quartz.CGImageMetadataRef:
    """Create a Quartz.CGImageMetadataRef from serialized XMP.

    Args:
        xmp: bytes object containing serialized XMP

    Returns: Quartz.CGImageMetadataRef

    Raises:
        MetadataError: If the metadata could not be created from the XMP data.

    Note: Quoted strings in the xmp data must use double quotes, not single quotes (apostrophes).
        The XMP standard allows strings in either format and exiftool uses single quotes but
        CGImageMetadataCreateFromXMPData returns nil if the XMP data contains single quotes.
        This does not appear to be documented anywhere in the Apple documentation.
        Also, the Apple documentation for CGImageMetadataCreateFromXMPData is incorrect;
        it states the XMP may contain the XMP packet header but if provided a valid XMP tree
        with packet header, the function returns nil.

        Reference: https://developer.apple.com/documentation/imageio/1465001-cgimagemetadatacreatefromxmpdata?language=objc
    """
    with objc.autorelease_pool():
        data = NSData.dataWithBytes_length_(xmp, len(xmp))
        metadata_ref = Quartz.CGImageMetadataCreateFromXMPData(data)
        if not metadata_ref:
            raise MetadataError("Could not create metadata from XMP data")
        del data
        return metadata_ref

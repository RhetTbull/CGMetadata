"""Utility functions for the project."""

from __future__ import annotations

import re

import AppKit
import objc
import UniformTypeIdentifiers
from Foundation import NSURL

from .types import FilePath


def is_image(filepath: FilePath) -> bool:
    """Return True if the file at `filepath` is an image file.

    Args:
        filepath: The path to the file to check.

    Returns: True if the file is an image file, False otherwise.

    Note: This function will work whether or not the file exists as the
    UTI is determined by the file extension.
    """

    # Cycle through all types associated with file and check if any of them are an image type
    # There are several APIs that would have made this easier but Apple has deprecated them all
    with objc.autorelease_pool():
        url = NSURL.fileURLWithPath_(str(filepath))
        provider = AppKit.NSItemProvider.alloc().initWithContentsOfURL_(url)
        registered_type_identifiers = provider.registeredTypeIdentifiers()
        image_type = UniformTypeIdentifiers.UTType.typeWithIdentifier_("public.image")
        for type_id in registered_type_identifiers:
            current_type = UniformTypeIdentifiers.UTType.typeWithIdentifier_(type_id)
            if current_type.conformsToType_(image_type):
                return True
        return False


def single_quotes_to_double_quotes(s: str) -> str:
    """Replace single quotes with double quotes in a string."""

    # this is a bit of hack

    # replace all escaped backslashes with a placeholder
    placeholder = "\u0000\u0001\u0000"
    s = s.replace(r"\\", placeholder)

    # replace all single quotes with double quotes except for escaped single quotes
    s = re.sub(r"(?<!\\)'", '"', s)

    # replace all placeholders with escaped backslashes
    s = s.replace(placeholder, r"\\")

    return s


def strip_xmp_packet(xmp: str) -> str:
    """Strip XMP packet header and footer from string.

    Args:
        xmp: An XMP string.

    Returns: The XMP string with the packet header and footer removed.
    """
    header_pattern = (
        r"<\?xpacket begin=['\"]\ufeff['\"] id=['\"]W5M0MpCehiHzreSzNTczkc9d['\"]\?>"
    )
    footer_pattern = r"<\?xpacket end=['\"]w['\"]\?>"

    xmp = re.sub(header_pattern, "", xmp)
    xmp = re.sub(footer_pattern, "", xmp)

    return xmp.strip()

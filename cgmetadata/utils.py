"""Utility functions for the project."""

from __future__ import annotations

import re
from typing import Any

import AppKit
import objc
from Foundation import NSURL, CFArrayRef, CFDataRef, CFDictionaryRef
from utitools import conforms_to_uti, uti_for_path

from .types import FilePath


def is_image(filepath: FilePath) -> bool:
    """Return True if the file at `filepath` is an image file.

    Args:
        filepath: The path to the file to check.

    Returns: True if the file is an image file, False otherwise.

    Note: This function will work whether or not the file exists as the
    UTI is determined by the file extension.
    """

    return conforms_to_uti(uti_for_path(filepath), "public.image")


def is_video(filepath: FilePath) -> bool:
    """Return True if the file at `filepath` is a video file.

    Args:
        filepath: The path to the file to check.

    Returns: True if the file is an video file, False otherwise.

    Note: This function will work whether or not the file exists as the
    UTI is determined by the file extension.
    """

    return conforms_to_uti(uti_for_path(filepath), "public.movie")


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


def cftype_to_pytype(value: Any) -> Any:
    """Convert a Core Foundation type to a python type
    This doesn't cover every type but covers types I've seen in metadata
    """
    if isinstance(value, NSURL):
        value = str(value.path())
    elif isinstance(value, objc.pyobjc_unicode):
        value = str(value)
    elif isinstance(value, CFDataRef):
        value = bytes(value)
    elif isinstance(value, objc._pythonify.OC_PythonLong):
        value = int(value)
    elif isinstance(value, objc._pythonify.OC_PythonFloat):
        value = float(value)
    elif isinstance(value, list):
        value = list(cftype_to_pytype(v) for v in value)
    return value


def CFDictionary_to_dict(cf_dict: CFDictionaryRef) -> dict:
    """Recursively convert a CFDictionary to a dict, converting any objective C types to python equivalent."""
    if cf_dict is None:
        return None
    d = {}
    for key, value in cf_dict.items():
        if isinstance(value, CFDictionaryRef):
            d[key] = CFDictionary_to_dict(value)
        else:
            if isinstance(value, CFArrayRef):
                value = list(cftype_to_pytype(v) for v in value)
            d[key] = cftype_to_pytype(value)
    return d

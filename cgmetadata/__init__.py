"""Use native Core Graphics API on macOS to access and change image metadata"""

from ._version import __version__
from .cgmetadata import MetadataError
from .classes import ImageMetadata
from .constants import EXIF, GPS, IPTC, TIFF, WEBP, XMP

__all__ = [
    "EXIF",
    "GPS",
    "IPTC",
    "ImageMetadata",
    "MetadataError",
    "TIFF",
    "WEBP",
    "XMP",
]

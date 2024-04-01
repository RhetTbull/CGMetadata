"""Use native Core Graphics / ImageIO API on macOS to access and change image metadata"""

from ._version import __version__
from .classes import ImageMetadata, ImageMetaData, VideoMetadata, VideoMetaData
from .constants import EXIF, GPS, IPTC, MDTA, TIFF, UDTA, XMP
from .metadata import MetadataError
from .xmp import metadata_dictionary_from_xmp_packet

__all__ = [
    "EXIF",
    "GPS",
    "ImageMetadata",
    "ImageMetaData",
    "IPTC",
    "is_xmp_packet",
    "MDTA",
    "metadata_dictionary_from_xmp_packet",
    "MetadataError",
    "TIFF",
    "UDTA",
    "VideoMetadata",
    "VideoMetaData",
    "XMP",
]

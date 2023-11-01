"""Use native Core Graphics API on macOS to access and change image metadata"""

from ._version import __version__
from .cgmetadata import MetadataError
from .classes import ImageMetadata

__all__ = ["ImageMetadata", "MetadataError"]

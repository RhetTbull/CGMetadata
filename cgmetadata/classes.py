"""Classes for CGMetadata"""

import os
from typing import IO, TYPE_CHECKING, Optional

from .cgmetadata import (
    MetadataError,
    load_image_metadata_dict,
    load_image_metadata_ref,
    load_image_properties,
    load_image_properties_dict,
    metadata_dictionary_from_image_metadata_ref,
    metadata_ref_create_empty_mutable,
    metadata_ref_create_from_xmp,
    metadata_ref_create_mutable_copy,
    metadata_ref_serialize_xmp,
)
from .types import CGMutableImageMetadataRef, FilePath
from .utils import is_image

XMP_PACKET_HEADER = "<?xpacket begin='?' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
XMP_PACKET_FOOTER = "<?xpacket end='w'?>\n"


class ImageMetadata:
    """Read and write image metadata properties using native macOS APIs."""

    def __init__(self, filepath: FilePath):
        self.filepath = filepath
        self._properties = load_image_properties(self.filepath)
        self._metadata_ref = load_image_metadata_ref(self.filepath)

    @property
    def properties(self):
        """Return the metadata properties dictionary from the image.

        The dictionary keys are named 'IPTC', 'EXIF', etc.
        Some of the values are themselves dictionaries.
        For example, the 'IPTC' value is a dictionary of IPTC metadata.

        Reference: https://developer.apple.com/documentation/imageio/image_properties?language=objc
        for more information.
        """

        # change keys to remove the leading '{' and trailing '}'
        # e.g. '{IPTC}' -> 'IPTC' but only if the key starts with '{'
        # also change Exif -> EXIF to match the other keys
        properties = {
            key[1:-1] if key.startswith("{") else key: value
            for key, value in self._properties.items()
        }
        if "Exif" in properties:
            properties["EXIF"] = properties.pop("Exif")
        return properties

    @property
    def exif(self):
        """Return the EXIF properties dictionary from the image."""
        return self.properties.get("EXIF", {})

    @property
    def iptc(self):
        """Return the IPTC properties dictionary from the image."""
        return self.properties.get("IPTC", {})

    @property
    def tiff(self):
        """Return the TIFF properties dictionary from the image."""
        return self.properties.get("TIFF", {})

    @property
    def gps(self):
        """Return the GPS properties dictionary from the image."""
        return self.properties.get("GPS", {})

    @property
    def xmp(self):
        """Get the XMP metadata dictionary for the image.

        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
        """
        return metadata_dictionary_from_image_metadata_ref(self._metadata_ref)

    def xmp_dumps(self, header: bool = True) -> str:
        """Return the serialized XMP metadata for the image."""
        xmp = metadata_ref_serialize_xmp(self._metadata_ref)
        if header:
            xmp = XMP_PACKET_HEADER + xmp.decode("utf-8") + XMP_PACKET_FOOTER
        return xmp

    def xmp_dump(self, fd: IO[str], header: bool = True):
        """Write the serialized XMP metadata for the image to a file."""
        xmp = metadata_ref_serialize_xmp(self._metadata_ref)
        if header:
            xmp = XMP_PACKET_HEADER + xmp.decode("utf-8") + XMP_PACKET_FOOTER
        fd.write(xmp)

    def __del__(self):
        if self._metadata_ref is not None:
            del self._metadata_ref
        if self._properties is not None:
            del self._properties


class XMPMetadata:
    """Read and write image metadata properties using native macOS APIs.

    Args:
        filepath: The path to the image file or the XMP sidecar file.
            If None, the metadata will be initialized with an empty dictionary.
    """

    def __init__(self, filepath: FilePath | None = None):
        self.filepath = filepath
        self.init_with_image = is_image(filepath) if filepath else False
        self.init_with_xmp = not self.init_with_image and filepath is not None
        self._metadata_ref = self._load_metadata_ref()

    @property
    def metadata(self):
        """Get the XMP metadata dictionary for the image.

        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
        """
        return self._metadata_ref

    def serialize(self, header: bool = True) -> str:
        """Return the serialized XMP metadata for the image.

        Args:
            header: If True, include the XMP packet header in the serialized XMP.

        Returns: The serialized XMP metadata for the image as a string.
        """
        xmp = metadata_ref_serialize_xmp(self._metadata_ref)

        xmp = xmp.decode("utf-8")
        if header:
            xmp = XMP_PACKET_HEADER + xmp

        return xmp

    def _load_metadata_ref(self) -> CGMutableImageMetadataRef:
        """Called by __init__ to load the metadata reference."""
        if self.init_with_image:
            metadata = load_image_metadata_ref(self.filepath)
            metadata_ref = metadata_ref_create_mutable_copy(metadata)
            del metadata
        elif self.init_with_xmp:
            xmp = open(self.filepath, "r").read()
            xmp = xmp.encode("utf-8")
            metadata = metadata_ref_create_from_xmp(xmp)
            metadata_ref = metadata_ref_create_mutable_copy(metadata)
            del metadata
        else:
            metadata_ref = metadata_ref_create_empty_mutable()
        return metadata_ref

    def __del__(self):
        if self._metadata_ref is not None:
            del self._metadata_ref

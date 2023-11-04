"""Classes for CGMetadata"""

import pathlib
from typing import IO, Any, Literal

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
    metadata_ref_set_tag,
    metadata_ref_write_to_file,
)
from .constants import (
    EXIF,
    GPS,
    IPTC,
    TIFF,
    WEBP,
    XMP,
    XMP_PACKET_FOOTER,
    XMP_PACKET_HEADER,
)
from .types import CGMutableImageMetadataRef, FilePath
from .utils import single_quotes_to_double_quotes, strip_xmp_packet


class ImageMetadata:
    """Read and write image metadata properties using native macOS APIs."""

    def __init__(self, filepath: FilePath):
        self.filepath = pathlib.Path(filepath).resolve()
        self._context_manager = False
        self._load()

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
        # also change Exif -> EXIF, WebP -> WEBP to match the other keys
        properties = {
            key[1:-1] if key.startswith("{") else key: value
            for key, value in self._properties.items()
        }
        if "Exif" in properties:
            properties["EXIF"] = properties.pop("Exif")
        if "WebP" in properties:
            properties["WEBP"] = properties.pop("WebP")
        return properties

    @property
    def exif(self):
        """Return the EXIF properties dictionary from the image."""
        return self.properties.get(EXIF, {})

    @property
    def iptc(self):
        """Return the IPTC properties dictionary from the image."""
        return self.properties.get(IPTC, {})

    @property
    def tiff(self):
        """Return the TIFF properties dictionary from the image."""
        return self.properties.get(TIFF, {})

    @property
    def gps(self):
        """Return the GPS properties dictionary from the image."""
        return self.properties.get(GPS, {})

    @property
    def webp(self):
        """Return the WebP properties dictionary from the image."""
        return self.properties.get(WEBP, {})

    @property
    def xmp(self):
        """Return the XMP metadata dictionary for the image.

        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
        """
        return metadata_dictionary_from_image_metadata_ref(self._metadata_ref)

    def xmp_dumps(self, header: bool = True) -> str:
        """Return the serialized XMP metadata for the image.

        Args:
            header: If True, include the XMP packet header in the serialized XMP.

        Returns:
            The serialized XMP metadata for the image as a string.
        """
        xmp = metadata_ref_serialize_xmp(self._metadata_ref).decode("utf-8")
        if header:
            xmp = f"{XMP_PACKET_HEADER}\n{xmp}\n{XMP_PACKET_FOOTER}"
        return xmp

    def xmp_dump(self, fp: IO[str], header: bool = True):
        """Write the serialized XMP metadata for the image to a file.

        Args:
            fp: The file pointer to write the XMP metadata to.
            header: If True, include the XMP packet header in the serialized XMP.
        """
        xmp = metadata_ref_serialize_xmp(self._metadata_ref).decode("utf-8")
        if header:
            xmp = XMP_PACKET_HEADER + xmp + XMP_PACKET_FOOTER
        fp.write(xmp)

    def xmp_loads(self, xmp: str):
        """Load XMP metadata from a string.

        Args:
            xmp: The XMP metadata as a string.
            fix_quotes: If True, replace single quotes with double quotes.

        Note: This does not write the metadata to the image file.
            Use write() to write the loaded metadata to the image file.
            The XMP standard allows quoted strings to use either single or double quotes.
            For example, exiftool uses single quotes. However, the native macOS APIs
            (CGImageMetadataCreateFromXMPData) returns nil if the XMP data contains single quotes.
            This does not appear to be documented anywhere in the Apple documentation.
            This function replaces single quotes with double quotes to avoid this issue.
        """
        self._xmp_set_from_str(xmp)

    def xmp_load(self, fp: IO[str]):
        """Load XMP metadata from a file.

        Args:
            fp: The file pointer to read the XMP metadata from.

        Note: This does not write the metadata to the image file.
            Use write() to write the loaded metadata to the image file.
            The XMP standard allows quoted strings to use either single or double quotes.
            For example, exiftool uses single quotes. However, the native macOS APIs
            (CGImageMetadataCreateFromXMPData) returns nil if the XMP data contains single quotes.
            This does not appear to be documented anywhere in the Apple documentation.
            This function replaces single quotes with double quotes to avoid this issue.
        """
        xmp = fp.read()
        self._xmp_set_from_str(xmp)

    def set(self, metadata_type: Literal["XMP", "EXIF"], key: str, value: Any):
        """Set a metadata property for the image.

        Args:
            metadata_type: The type of metadata to set, either "XMP" or "EXIF".
            key: The key path of the metadata property to set; e.g. "dc:creator".
            value: The value to set the metadata property to.

        Note: This does not write the metadata to the image file unless used
            in conjunction with the context manager. Use write() to write the
            metadata to the image file.
        """
        if metadata_type == XMP:
            self._metadata_ref = metadata_ref_set_tag(self._metadata_ref, key, value)
        elif metadata_type == EXIF:
            raise NotImplementedError("set EXIF metadata not implemented")
        else:
            raise MetadataError(f"unknown metadata type: {metadata_type}")

    def write(self):
        """Write the metadata to the image file."""

        # TODO: currently only handles XMP metadata
        metadata_ref_write_to_file(self.filepath, self._metadata_ref)

    def reload(self):
        """Reload the metadata from the image file."""
        self._load()

    def asdict(self) -> dict[str, Any]:
        """Return the metadata as a dictionary."""
        dict_data = self.properties
        dict_data[XMP] = self.xmp
        return dict_data

    def _load(self):
        try:
            del self._metadata_ref
        except AttributeError:
            pass
        try:
            del self._properties
        except AttributeError:
            pass
        self._properties = load_image_properties(self.filepath)
        metadata_ref = load_image_metadata_ref(self.filepath)
        self._metadata_ref = metadata_ref_create_mutable_copy(metadata_ref)
        del metadata_ref

    def _xmp_set_from_str(self, xmp: str):
        """Set the XMP metadata from a string representing serialized XMP."""

        # The Apple API requires that the XMP data use double quotes for quoted strings
        # and that the XMP data not contain the XMP packet headers
        xmp = single_quotes_to_double_quotes(xmp)
        xmp = strip_xmp_packet(xmp)
        xmp = xmp.encode("utf-8")
        self._xmp_set_from_bytes(xmp)

    def _xmp_set_from_bytes(self, xmp: bytes):
        """Set the XMP metadata from a bytes object representing serialized XMP."""
        metadata = metadata_ref_create_from_xmp(xmp)
        del self._metadata_ref
        self._metadata_ref = metadata_ref_create_mutable_copy(metadata)
        del metadata

    def __enter__(self):
        """Enter the context manager."""
        self._context_manager = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        if self._context_manager:
            self.write()
            self.reload()
        self._context_manager = False

    def __del__(self):
        if self._metadata_ref is not None:
            del self._metadata_ref
        if self._properties is not None:
            del self._properties


# class XMPMetadata:
#     """Read and write image metadata properties using native macOS APIs.

#     Args:
#         filepath: The path to the image file or the XMP sidecar file.
#             If None, the metadata will be initialized with an empty dictionary.
#     """

#     def __init__(self, filepath: FilePath | None = None):
#         self.filepath = filepath
#         self.init_with_image = is_image(filepath) if filepath else False
#         self.init_with_xmp = not self.init_with_image and filepath is not None
#         self._metadata_ref = self._load_metadata_ref()

#     @property
#     def metadata(self):
#         """Get the XMP metadata dictionary for the image.

#         The dictionary keys are in form "prefix:name", e.g. "dc:creator".
#         """
#         return self._metadata_ref

#     def serialize(self, header: bool = True) -> str:
#         """Return the serialized XMP metadata for the image.

#         Args:
#             header: If True, include the XMP packet header in the serialized XMP.

#         Returns: The serialized XMP metadata for the image as a string.
#         """
#         xmp = metadata_ref_serialize_xmp(self._metadata_ref)

#         xmp = xmp.decode("utf-8")
#         if header:
#             xmp = XMP_PACKET_HEADER + xmp

#         return xmp

#     def _load_metadata_ref(self) -> CGMutableImageMetadataRef:
#         """Called by __init__ to load the metadata reference."""
#         if self.init_with_image:
#             metadata = load_image_metadata_ref(self.filepath)
#             metadata_ref = metadata_ref_create_mutable_copy(metadata)
#             del metadata
#         elif self.init_with_xmp:
#             xmp = open(self.filepath, "r").read()
#             xmp = xmp.encode("utf-8")
#             metadata = metadata_ref_create_from_xmp(xmp)
#             metadata_ref = metadata_ref_create_mutable_copy(metadata)
#             del metadata
#         else:
#             metadata_ref = metadata_ref_create_empty_mutable()
#         return metadata_ref

#     def __del__(self):
#         if self._metadata_ref is not None:
#             del self._metadata_ref

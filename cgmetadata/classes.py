"""Classes for CGMetadata"""

import pathlib
from typing import IO, Any, Literal

from .cgmetadata import (
    load_image_metadata_ref,
    load_image_properties,
    load_video_metadata,
    load_video_xmp,
)
from .constants import (
    EXIF,
    GPS,
    IPTC,
    TIFF,
    UDTA,
    XMP,
    XMP_PACKET_FOOTER,
    XMP_PACKET_HEADER,
)
from .metadata import (
    metadata_dictionary_from_image_metadata_ref,
    metadata_ref_create_mutable_copy,
    metadata_ref_set_tag_for_dict,
    metadata_ref_set_tag_with_path,
    metadata_ref_write_to_file,
)
from .types import FilePath
from .utils import (
    CFDictionary_to_dict,
    is_image,
    is_video,
    single_quotes_to_double_quotes,
    strip_xmp_packet,
)
from .xmp import metadata_ref_create_from_xmp, metadata_ref_serialize_xmp


class ImageMetadata:
    """Read and write image metadata properties using native macOS APIs.

    Args:
        filepath: The path to the image file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not an image file.
    """

    def __init__(self, filepath: FilePath):
        self.filepath = pathlib.Path(filepath).resolve()
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        if not is_image(self.filepath):
            raise ValueError(f"Not an image file: {self.filepath}")
        self._context_manager = False
        self._load()

    @property
    def properties(self) -> dict[str, Any]:
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
        properties = CFDictionary_to_dict(self._properties)
        properties = {
            key[1:-1] if key.startswith("{") else key: value
            for key, value in properties.items()
        }
        if "Exif" in properties:
            properties["EXIF"] = properties.pop("Exif")
        if "WebP" in properties:
            properties["WEBP"] = properties.pop("WebP")
        return properties

    @property
    def exif(self) -> dict[str, Any]:
        """Return the EXIF properties dictionary from the image."""
        return self.properties.get(EXIF, {})

    @property
    def iptc(self) -> dict[str, Any]:
        """Return the IPTC properties dictionary from the image."""
        return self.properties.get(IPTC, {})

    @property
    def tiff(self) -> dict[str, Any]:
        """Return the TIFF properties dictionary from the image."""
        return self.properties.get(TIFF, {})

    @property
    def gps(self) -> dict[str, Any]:
        """Return the GPS properties dictionary from the image."""
        return self.properties.get(GPS, {})

    @property
    def xmp(self) -> dict[str, Any]:
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

        Note:
            This does not write the metadata to the image file.
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

        Note:
            This does not write the metadata to the image file.
            Use write() to write the loaded metadata to the image file.
            The XMP standard allows quoted strings to use either single or double quotes.
            For example, exiftool uses single quotes. However, the native macOS APIs
            (CGImageMetadataCreateFromXMPData) returns nil if the XMP data contains single quotes.
            This does not appear to be documented anywhere in the Apple documentation.
            This function replaces single quotes with double quotes to avoid this issue.
        """
        xmp = fp.read()
        self._xmp_set_from_str(xmp)

    def set(
        self,
        group: Literal["EXIF", "IPTC", "TIFF", "GPS", "XMP"],
        key: str,
        value: Any,
    ):
        """Set a metadata property for the image.

        Args:
            group: The metadata group type to set the property for, for example, "IPTC", "XMP"
            key: The key or key path of the metadata property to set;
                for "XMP" metadata, the key is in form "prefix:name", e.g. "dc:creator", "dc:description"...
                for other metadata, the key is the name of the property, e.g. "LensModel", "Make", "Keywords"...
            value: The value to set the metadata property to.

        Note:
            This does not write the metadata to the image file unless used in conjunction with the context manager.
            Use write() to write the metadata to the image file after setting one or more values.
            Metadata keys may be specified as a literal string, e.g. "LensModel" or using
            one of the constants from the ImageIO module, e.g. kCGImagePropertyExifLensModel,
            which are referenced here: https://developer.apple.com/documentation/imageio/exif_dictionary_keys
            These are available in the pyobjc Quartz module as Quartz.kCGImagePropertyExifLensModel, etc.
            You are responsible for passing the correct type of value for the metadata key,
            for example, str or list[str]. See https://github.com/adobe/xmp-docs/tree/master
            for more information on XMP metadata and expected types.
        """
        if group == XMP:
            self._metadata_ref = metadata_ref_set_tag_with_path(
                self._metadata_ref, key, value
            )
        else:
            self._metadata_ref = metadata_ref_set_tag_for_dict(
                self._metadata_ref, group, key, value
            )

    def write(self):
        """Write the metadata to the image file then reloads the metadata from the image."""
        metadata_ref_write_to_file(self.filepath, self._metadata_ref)
        self.reload()

    def reload(self):
        """Reload the metadata from the image file."""
        self._load()

    def asdict(self) -> dict[str, Any]:
        """Return the metadata as a dictionary."""
        dict_data = self.properties.copy()
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
        properties = load_image_properties(self.filepath)
        self._properties = properties.mutableCopy()
        del properties

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


class ImageMetaData(ImageMetadata):
    """Alias for ImageMetadata."""

    pass


class VideoMetadata:
    """Read video metadata properties using native macOS APIs.

    Args:
        filepath: The path to the video file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not an video file.

    Note: Unlike ImageMetadata, this class does not provide write access to the metadata.
    """

    def __init__(self, filepath: FilePath):
        self.filepath = pathlib.Path(filepath).resolve()
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        if not is_video(self.filepath):
            raise ValueError(f"Not a video file: {self.filepath}")
        self._context_manager = False
        self._load()

    @property
    def properties(self) -> dict[str, Any]:
        """Return the metadata properties dictionary from the image.

        The dictionary keys are named with the namespace, such as 'mdta', 'udta'.
        Some of the values are themselves dictionaries.
        """
        return self._properties

    @property
    def xmp(self) -> dict[str, Any]:
        """Return the XMP metadata dictionary for the image.

        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
        """
        return self._properties.get(XMP, {})

    def xmp_dumps(self, header: bool = True) -> str:
        """Return the serialized XMP metadata for the video.

        Args:
            header: If True, include the XMP packet header in the serialized XMP.

        Returns:
            The serialized XMP metadata for the image as a string.
        """
        xmp = self._xmp
        if not header:
            xmp = strip_xmp_packet(xmp)
        return xmp

    def xmp_dump(self, fp: IO[str], header: bool = True):
        """Write the serialized XMP metadata for the video to a file.

        Args:
            fp: The file pointer to write the XMP metadata to.
            header: If True, include the XMP packet header in the serialized XMP.
        """
        xmp = self.xmp_dumps(header)
        xmp = xmp.encode("utf-8")
        fp.write(xmp)

    def reload(self):
        """Reload the metadata from the image file."""
        self._load()

    def asdict(self) -> dict[str, Any]:
        """Return the metadata as a dictionary."""
        dict_data = self._properties.copy()
        return dict_data

    def _load(self):
        try:
            del self._properties
        except AttributeError:
            pass
        self._properties = load_video_metadata(self.filepath)
        self._xmp = load_video_xmp(self.filepath)


class VideoMetaData(VideoMetadata):
    """Alias for VideoMetadata."""

    pass


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

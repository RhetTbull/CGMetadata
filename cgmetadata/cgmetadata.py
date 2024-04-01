"""Use native Core Graphics API on macOS to access and change image metadata

This code is an alternative to using a third-party tool like the excellent [exiftool](https://exiftool.org/)
and uses Apple's native ImageIO APIs. It should be able to read metadata from any file format supported
by ImageIO.

Implementation Note: Core Foundation objects created with Create or Copy functions must be released;
this is done with `del Object` in pyobjc.
"""

from __future__ import annotations

from typing import Any

import objc
import Quartz
from AVFoundation import AVURLAsset
from CoreFoundation import CFDictionaryCreate, CFDictionaryRef
from Foundation import NSURL

from .constants import MDTA, UDTA, XMP
from .iso6709 import parse_iso_6709
from .metadata import (
    NSDictionary_to_dict_recursive,
    metadata_dictionary_from_image_metadata_ref,
)
from .types import FilePath
from .xmp import is_xmp_packet, metadata_dictionary_from_xmp_packet


def load_image_properties(
    image_path: FilePath,
) -> CFDictionaryRef:
    """Return the metadata properties dictionary from the image at the given path.

    Args:
        image_path: Path to the image file.

    Returns:
        A CFDictionary dictionary of metadata properties from the image file.
        If the image does not contain metadata, an empty CFDictionary is returned.

    Note:
        The dictionary keys are named '{IPTC}', '{TIFF}', etc.
        Reference: https://developer.apple.com/documentation/imageio/image_properties?language=objc
        for more information.

        This function is useful for retrieving EXIF and IPTC metadata.
    """
    with objc.autorelease_pool():
        image_url = NSURL.fileURLWithPath_(str(image_path))
        image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)

        metadata = Quartz.CGImageSourceCopyPropertiesAtIndex(image_source, 0, None)
        del image_source
        return metadata or CFDictionaryCreate(None, [], [], 0, None, None)


def load_image_properties_dict(
    image_path: FilePath,
) -> dict[str, Any]:
    """Return the metadata properties dictionary from the image at the given path.

    Args:
        image_path: Path to the image file.

    Returns:
        A dictionary of metadata properties from the image file.

    Note:
        The dictionary keys are named '{IPTC}', '{TIFF}', etc.
        Reference: https://developer.apple.com/documentation/imageio/image_properties?language=objc
        for more information.

        This function is useful for retrieving EXIF and IPTC metadata.
    """
    metadata = load_image_properties(image_path)
    return NSDictionary_to_dict_recursive(metadata)


def load_image_metadata_dict(
    image_path: FilePath,
) -> dict[str, Any]:
    """Get the XMP metadata from the image at the given path

    Args:
        image_path: Path to the image file.

    Returns:
        A dictionary of XMP metadata properties from the image file.
        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
    """
    metadata = load_image_metadata_ref(str(image_path))
    return metadata_dictionary_from_image_metadata_ref(metadata) if metadata else {}


def load_image_metadata_ref(
    image_path: FilePath,
) -> Quartz.CGImageMetadataRef:
    """Get the Quartz.CGImageMetadataRef from the image at the given path

    Args:
        image_path: Path to the image file.

    Returns:
        A Quartz.CGImageMetadataRef containing the XMP metadata.
        If the image does not contain metadata, an empty Quartz.CGImageMetadataRef is returned.
    """
    with objc.autorelease_pool():
        image_url = NSURL.fileURLWithPath_(str(image_path))
        image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)

        metadata = Quartz.CGImageSourceCopyMetadataAtIndex(image_source, 0, None)
        del image_source
    return metadata or Quartz.CGImageMetadataCreateMutable()


def load_image_location(
    image_path: FilePath,
) -> tuple[float, float]:
    """Return the GPS latitude/longitude coordinates from the image at the given path.

    Args:
        image_path: Path to the image file.

    Returns:
        A tuple of latitude and longitude.

    Raises:
        ValueError: If the image does not contain GPS data or if the GPS data does not contain latitude and longitude.
    """
    properties = load_image_properties_dict(image_path)
    gps_data = properties.get(Quartz.kQuartz.CGImagePropertyGPSDictionary)
    if not gps_data:
        raise ValueError("This image does not contain GPS data")

    latitude = gps_data.get(Quartz.kQuartz.CGImagePropertyGPSLatitude)
    longitude = gps_data.get(Quartz.kQuartz.CGImagePropertyGPSLongitude)

    if latitude is None or longitude is None:
        raise ValueError("Could not extract latitude and/or longitude from GPS data")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        raise ValueError("Could not extract latitude and/or longitude from GPS data")

    if gps_data.get(Quartz.kQuartz.CGImagePropertyGPSLatitudeRef) == "S":
        latitude *= -1
    if gps_data.get(Quartz.kQuartz.CGImagePropertyGPSLongitudeRef) == "W":
        longitude *= -1

    return latitude, longitude


def load_video_metadata(video_path: FilePath) -> dict[str, Any]:
    """Load metadata from a video file using AVFoundation.

    Args:
        video_path: Path to a video file.

    Returns: A dictionary of metadata key-value pairs.
    """
    with objc.autorelease_pool():
        video_path = str(video_path)
        video_url = NSURL.fileURLWithPath_(video_path)
        asset = AVURLAsset.URLAssetWithURL_options_(video_url, None)

        metadata_formats = asset.availableMetadataFormats()
        metadata_dictionary = {}

        for format in metadata_formats:
            metadata_items = asset.metadataForFormat_(format)

            for item in metadata_items:
                namespace = str(item.keySpace()) if item.keySpace() else ""
                if key := item.commonKey():
                    key = str(key)
                    key = key[0].upper() + key[1:] if len(key) > 1 else key.upper()
                else:
                    key = ""  # I've seen null key
                value = item.value()
                if namespace not in metadata_dictionary:
                    metadata_dictionary[namespace] = {}
                if value is not None:
                    if namespace == UDTA and not key:
                        # user data, possibly an XMP packet
                        if is_xmp_packet(value):
                            metadata_dictionary[XMP] = (
                                metadata_dictionary_from_xmp_packet(value)
                            )
                        else:
                            metadata_dictionary[namespace][key] = str(value)
                    elif namespace == MDTA and key == "Location":
                        try:
                            coordinates = parse_iso_6709(value)
                            metadata_dictionary[namespace][key] = {
                                "Latitude": coordinates[0],
                                "Longitude": coordinates[1],
                                "Height": coordinates[2],
                                "CRS": coordinates[3],
                            }
                        except ValueError:
                            metadata_dictionary[namespace][key] = str(value)
                    else:
                        metadata_dictionary[namespace][key] = str(value)
        return metadata_dictionary


def load_video_xmp(video_path: FilePath) -> str | None:
    """Load XMP metadata packet from a video file using AVFoundation.

    Args:
        video_path: Path to a video file.

    Returns: str containing the XMP metadata packet.
    """
    with objc.autorelease_pool():
        video_path = str(video_path)
        video_url = NSURL.fileURLWithPath_(video_path)
        asset = AVURLAsset.URLAssetWithURL_options_(video_url, None)

        metadata_formats = asset.availableMetadataFormats()

        for format in metadata_formats:
            metadata_items = asset.metadataForFormat_(format)

            for item in metadata_items:
                namespace = str(item.keySpace()) if item.keySpace() else ""
                if key := item.commonKey():
                    key = str(key)
                    key = key[0].upper() + key[1:] if len(key) > 1 else key.upper()
                else:
                    key = ""  # I've seen null key
                value = item.value()
                if value is not None:
                    if namespace == UDTA and not key:
                        # user data, possibly an XMP packet
                        if is_xmp_packet(value):
                            return value.decode("utf-8")
    return None


# def load_image_auxilary_data(image_path: FilePath) -> CFDictionaryRef:
#     """Return the auxiliary data dictionary from the image at the given path."""
#     with objc.autorelease_pool():
#         image_url = NSURL.fileURLWithPath_(str(image_path))
#         image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)

#         aux_data = Quartz.CGImageSourceCopyAuxiliaryDataInfoAtIndex(
#             image_source, 0, Quartz.kCGImageAuxiliaryDataTypeXMP
#         )
#         del image_source
#         return aux_data


# def image_file_write_properties_metadata(
#     image_path: FilePath,
#     properties: CFDictionaryRef,
#     metadata_ref: Quartz.CGImageMetadataRef,
# ) -> None:
#     """Write properties and metadata to an image file."""
#     with objc.autorelease_pool():
#         image_url = NSURL.fileURLWithPath_(str(image_path))
#         image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
#         if not image_source:
#             raise MetadataError(f"Could not create image source for {image_path}")
#         image_type = Quartz.CGImageSourceGetType(image_source)
#         destination = Quartz.CGImageDestinationCreateWithURL(
#             image_url, image_type, 1, None
#         )
#         if not destination:
#             raise MetadataError(f"Could not create image destination for {image_path}")
#         with pipes() as (_out, _err):
#             # On some versions of macOS this causes error to stdout
#             # of form: AVEBridge Info: AVEEncoder_CreateInstance: Received CreateInstance (from VT)...
#             # even though the operation succeeds
#             # Use pipes() to suppress this error
#             image_data = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
#             Quartz.CGImageDestinationAddImageAndMetadata(
#                 destination,
#                 image_data,
#                 metadata_ref,
#                 None,
#             )
#             Quartz.CGImageDestinationSetProperties(destination, properties)
#             Quartz.CGImageDestinationFinalize(destination)
#         del image_source
#         del image_data
#         del destination

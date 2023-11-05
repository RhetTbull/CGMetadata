"""Use native Core Graphics API on macOS to access and change image metadata

This code is an alternative to using a third-party tool like the excellent [exiftool](https://exiftool.org/)
and uses Apple's native ImageIO APIs. It should be able to read metadata from any file format supported
by ImageIO.

Implementation Note: Core Foundation objects created with Create or Copy functions must be released;
this is done with `del Object` in pyobjc.
"""

from __future__ import annotations

from typing import Any, Literal

import objc
import Quartz
from CoreFoundation import (
    CFArrayGetCount,
    CFArrayGetTypeID,
    CFArrayGetValueAtIndex,
    CFDictionaryCreate,
    CFDictionaryGetTypeID,
    CFDictionaryRef,
    CFGetTypeID,
    CFStringCreateCopy,
    CFStringGetTypeID,
)
from Foundation import (
    NSURL,
    NSArray,
    NSData,
    NSDictionary,
    NSMutableArray,
    NSMutableDictionary,
)
from wurlitzer import pipes

from .types import CGMutableImageMetadataRef, FilePath


class MetadataError(Exception):
    """Error calling Quartz.CGImageMetadata functions."""

    pass


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


def metadata_ref_create_mutable_copy(
    metadata_ref: Quartz.CGImageMetadataRef | CGMutableImageMetadataRef,
) -> CGMutableImageMetadataRef:
    """Create a CGMutableImageMetadataRef copy from a Quartz.CGImageMetadataRef."""
    with objc.autorelease_pool():
        return Quartz.CGImageMetadataCreateMutableCopy(metadata_ref)


def metadata_ref_create_empty_mutable() -> CGMutableImageMetadataRef:
    """Create an empty CGMutableImageMetadataRef."""
    with objc.autorelease_pool():
        return Quartz.CGImageMetadataCreateMutable()


def metadata_ref_set_tag_with_path(
    metadata_ref: CGMutableImageMetadataRef,
    tag_path: str,
    value: Any,
) -> CGMutableImageMetadataRef:
    """Set a metadata tag to value in a CGMutableImageMetadataRef

    Args:
        metadata_ref: A CGMutableImageMetadataRef
        tag_path: The tag path to set
        value: The value to set

    Returns: CGMutableImageMetadataRef with the tag set to value
    """
    with objc.autorelease_pool():
        if Quartz.CGImageMetadataSetValueWithPath(metadata_ref, None, tag_path, value):
            return metadata_ref
        raise MetadataError(
            f"Could not set tag {tag_path} to {value}; "
            "verify the tag and value are valid and that metadata_ref is a CGMutableImageMetadataRef"
        )


def metadata_ref_set_tag_for_dict(
    metadata_ref: CGMutableImageMetadataRef,
    dictionary: Literal[
        "EXIF",
        "IPTC",
        "XMP",
        "TIFF",
        "GPS",
        "WEBP",
        "HEIC",
        "CIFF",
        "DNG",
        "GIF",
        "JFIF",
        "PNG",
        "TGA",
        "8BIM",
    ],
    tag: str,
    value: Any,
) -> CGMutableImageMetadataRef:
    """Set a metadata tag to value in a CGMutableImageMetadataRef for the given dictionary

    Args:
        metadata_ref: A CGMutableImageMetadataRef
        dictionary: The dictionary to set (e.g. "EXIF", "IPTC", "XMP", "TIFF", "GPS")
        tag: The tag to set
        value: The value to set

    Returns: CGMutableImageMetadataRef with the tag set to value
    """
    dict_names = {
        "EXIF": Quartz.kCGImagePropertyExifDictionary,
        "IPTC": Quartz.kCGImagePropertyIPTCDictionary,
        "GPS": Quartz.kCGImagePropertyGPSDictionary,
        "WEBP": Quartz.kCGImagePropertyWebPDictionary,
        "HEIC": Quartz.kCGImagePropertyHEICSDictionary,
        "CIFF": Quartz.kCGImagePropertyCIFFDictionary,
        "DNG": Quartz.kCGImagePropertyDNGDictionary,
        "GIF": Quartz.kCGImagePropertyGIFDictionary,
        "JFIF": Quartz.kCGImagePropertyJFIFDictionary,
        "PNG": Quartz.kCGImagePropertyPNGDictionary,
        "TGA": Quartz.kCGImagePropertyTGADictionary,
        "TIFF": Quartz.kCGImagePropertyTIFFDictionary,
        "8BIM": Quartz.kCGImageProperty8BIMDictionary,
    }
    dict_name = dict_names.get(dictionary.upper())
    if not dict_name:
        raise MetadataError(f"Invalid dictionary {dictionary}")

    with objc.autorelease_pool():
        if Quartz.CGImageMetadataSetValueMatchingImageProperty(
            metadata_ref, dict_name, tag, value
        ):
            return metadata_ref
        raise MetadataError(
            f"Could not set tag {tag} to {value} for dictionary {dict_name}; "
            "verify the dictionary, tag, and value are valid and that metadata_ref is a CGMutableImageMetadataRef"
        )


def metadata_ref_write_to_file(
    image_path: FilePath,
    metadata_ref: Quartz.CGImageMetadataRef,
) -> None:
    """Write metadata to an image file.

    Args:
        image_path: Path to the image file.
        metadata_ref: A CGImageMetadataRef containing the metadata to write.
    """
    with objc.autorelease_pool():
        image_url = NSURL.fileURLWithPath_(str(image_path))
        image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
        if not image_source:
            raise MetadataError(f"Could not create image source for {image_path}")
        image_type = Quartz.CGImageSourceGetType(image_source)
        destination = Quartz.CGImageDestinationCreateWithURL(
            image_url, image_type, 1, None
        )
        if not destination:
            raise MetadataError(f"Could not create image destination for {image_path}")
        with pipes() as (_out, _err):
            # On some versions of macOS this causes error to stdout
            # of form: AVEBridge Info: AVEEncoder_CreateInstance: Received CreateInstance (from VT)...
            # even though the operation succeeds
            # Use pipes() to suppress this error
            image_data = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
            Quartz.CGImageDestinationAddImageAndMetadata(
                destination,
                image_data,
                metadata_ref,
                None,
            )
            Quartz.CGImageDestinationFinalize(destination)

        del destination
        del image_data
        del image_source


def properties_dict_write_to_file(
    image_path: FilePath,
    properties: CFDictionaryRef,
) -> None:
    """Write properties to an image file.

    Args:
        image_path: Path to the image file.
        properties: A CFDictionaryRef containing the properties to write.
    """
    with objc.autorelease_pool():
        image_url = NSURL.fileURLWithPath_(str(image_path))
        image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
        if not image_source:
            raise MetadataError(f"Could not create image source for {image_path}")
        image_type = Quartz.CGImageSourceGetType(image_source)
        destination = Quartz.CGImageDestinationCreateWithURL(
            image_url, image_type, 1, None
        )
        if not destination:
            raise MetadataError(f"Could not create image destination for {image_path}")
        with pipes() as (_out, _err):
            # On some versions of macOS this causes error to stdout
            # of form: AVEBridge Info: AVEEncoder_CreateInstance: Received CreateInstance (from VT)...
            # even though the operation succeeds
            # Use pipes() to suppress this error
            image_data = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
            Quartz.CGImageDestinationAddImageFromSource(
                destination, image_source, 0, properties
            )
            Quartz.CGImageDestinationFinalize(destination)

        del destination
        del image_data
        del image_source


def properties_dict_set_tag(
    properties_dict: CFDictionaryRef, sub_dict: str | None, tag: str, value: Any
) -> CFDictionaryRef:
    """Set a tag to value in a CFDictionaryRef as returned by load_image_properties.

    Args:
        properties_dict: A CFDictionaryRef
        sub_dict: The sub dictionary to set or None if the tag is not in a sub dictionary
        tag: The tag to set
        value: The value to set

    Returns: CFDictionaryRef with the tag set to value
    """
    mutable_dict = properties_dict.mutableCopy()
    if sub_dict:
        dict_ref = mutable_dict[sub_dict].mutableCopy()
        if not dict_ref:
            dict_ref = NSMutableDictionary.dictionary()
        dict_ref[tag] = value
        mutable_dict[sub_dict] = dict_ref
        return mutable_dict

    mutable_dict[tag] = value
    return mutable_dict


def NSDictionary_to_dict_recursive(ns_dict: NSDictionary) -> dict[str, Any]:
    """Convert an NSDictionary to a Python dict recursively; handles subset of types needed for image metadata."""
    py_dict = {}
    for key, value in ns_dict.items():
        if isinstance(value, NSDictionary):
            py_dict[key] = NSDictionary_to_dict_recursive(value)
        elif isinstance(value, NSArray):
            py_dict[key] = NSArray_to_list_recursive(value)
        elif isinstance(value, NSData):
            py_dict[key] = value.bytes().tobytes()
        else:
            py_dict[key] = str(value)
    return py_dict


def NSArray_to_list_recursive(ns_array: NSArray) -> list[Any]:
    """Convert an NSArray to a Python list recursively; handles subset of types needed for image metadata."""
    py_list = []
    for value in ns_array:
        if isinstance(value, NSDictionary):
            py_list.append(NSDictionary_to_dict_recursive(value))
        elif isinstance(value, NSArray):
            py_list.append(NSArray_to_list_recursive(value))
        elif isinstance(value, NSData):
            py_list.append(value.bytes().tobytes())
        else:
            py_list.append(str(value))
    return py_list


def metadata_dictionary_from_image_metadata_ref(
    metadata_ref: Quartz.CGImageMetadataRef,
) -> dict[str, Any]:
    with objc.autorelease_pool():
        tags = Quartz.CGImageMetadataCopyTags(metadata_ref)
        if not tags:
            return {}

        metadata_dict = {}
        for i in range(CFArrayGetCount(tags)):
            tag = CFArrayGetValueAtIndex(tags, i)

            prefix = Quartz.CGImageMetadataTagCopyPrefix(tag)
            name = Quartz.CGImageMetadataTagCopyName(tag)
            value = Quartz.CGImageMetadataTagCopyValue(tag)

            key = f"{prefix}:{name}"
            object_value = _recursive_parse_metadata_value(value)
            metadata_dict[key] = object_value

        return metadata_dict.copy()


def _recursive_parse_metadata_value(value: Any) -> Any:
    if CFGetTypeID(value) == CFStringGetTypeID():
        return str(value)
    elif CFGetTypeID(value) == CFDictionaryGetTypeID():
        value_dict = NSMutableDictionary.dictionary()
        original_dict = NSDictionary.dictionaryWithDictionary_(value)
        for key in original_dict.allKeys():
            value_dict[key] = _recursive_parse_metadata_value(original_dict[key])
        return NSDictionary_to_dict_recursive(value_dict)
    elif CFGetTypeID(value) == CFArrayGetTypeID():
        value_array = NSMutableArray.array()
        original_array = NSArray.arrayWithArray_(value)
        for element in original_array:
            value_array.addObject_(_recursive_parse_metadata_value(element))
        return NSArray_to_list_recursive(value_array)
    elif CFGetTypeID(value) == Quartz.CGImageMetadataTagGetTypeID():
        tag_value = Quartz.CGImageMetadataTagCopyValue(value)
        return _recursive_parse_metadata_value(tag_value)
    else:
        return value


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

"""Utilities for working with CGMetadataRef"""

from __future__ import annotations

from typing import Any, Literal

import objc
import Quartz
from CoreFoundation import (
    CFArrayGetCount,
    CFArrayGetTypeID,
    CFArrayGetValueAtIndex,
    CFDictionaryGetTypeID,
    CFDictionaryRef,
    CFGetTypeID,
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

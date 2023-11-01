"""Utility functions for the project."""

from __future__ import annotations

import AppKit
import objc
import UniformTypeIdentifiers
from Foundation import NSURL

from .types import FilePath


def is_image(filepath: FilePath) -> bool:
    """Return True if the file at `filepath` is an image file.

    Args:
        filepath: The path to the file to check.

    Returns: True if the file is an image file, False otherwise.

    Note: This function will work whether or not the file exists as the
    UTI is determined by the file extension.
    """

    # Cycle through all types associated with file and check if any of them are an image type
    # There are several APIs that would have made this easier but Apple has deprecated them all
    with objc.autorelease_pool():
        url = NSURL.fileURLWithPath_(str(filepath))
        provider = AppKit.NSItemProvider.alloc().initWithContentsOfURL_(url)
        registered_type_identifiers = provider.registeredTypeIdentifiers()
        image_type = UniformTypeIdentifiers.UTType.typeWithIdentifier_("public.image")
        for type_id in registered_type_identifiers:
            current_type = UniformTypeIdentifiers.UTType.typeWithIdentifier_(type_id)
            if current_type.conformsToType_(image_type):
                return True
        return False

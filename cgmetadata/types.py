"""Custom types for the project."""

import os
import pathlib
from typing import TypeVar

import Quartz

# Acccept any type that can be converted to a path
FilePath = TypeVar("FilePath", str, pathlib.Path, os.PathLike)

# Create a custom type for CGMutableImageMetadataRef
# This is used to indicate which functions require a mutable copy of the metadata
# The Quartz package doesn't provide a CGMutableImageMetadataRef type
CGMutableImageMetadataRef = Quartz.CGImageMetadataRef

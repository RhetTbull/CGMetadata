"""Classes for CGMetadata"""

from .cgmetadata import (
    FilePath,
    MetadataError,
    load_image_metadata,
    load_image_metadata_ref,
    load_image_properties,
    metadata_ref_create_xmp,
)


class ImageProperties:
    """Read and write image metadata properties using native macOS APIs."""

    def __init__(self, filepath: FilePath):
        self.filepath = filepath

    @property
    def properties(self):
        """Return the metadata properties dictionary from the image.

        The dictionary keys are named 'IPTC', 'EXIF', etc.
        Some of the values are themselves dictionaries.
        For example, the 'IPTC' value is a dictionary of IPTC metadata.

        Reference: https://developer.apple.com/documentation/imageio/image_properties?language=objc
        for more information.
        """
        properties = load_image_properties(self.filepath)

        # change keys to remove the leading '{' and trailing '}'
        # e.g. '{IPTC}' -> 'IPTC' but only if the key starts with '{'
        # also change Exif -> EXIF to match the other keys
        properties = {
            key[1:-1] if key.startswith("{") else key: value
            for key, value in properties.items()
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
    def metadata(self):
        """Get the XMP metadata dictionary for the image.

        The dictionary keys are in form "prefix:name", e.g. "dc:creator".
        """
        return load_image_metadata(self.filepath)

    def xmp(self):
        """Return the serialized XMP metadata for the image."""
        metadata_ref = load_image_metadata_ref(self.filepath)
        return metadata_ref_create_xmp(metadata_ref)

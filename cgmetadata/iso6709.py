"""Work with ISO 6709 coordinate strings."""

import re


def parse_iso_6709(iso_6709_str: str) -> tuple[float, float, float | None, str | None]:
    """
    Parse an ISO 6709 string and return latitude and longitude as floats.

    The ISO 6709 string should be in the format: '+33.9180-118.3814+039.512/'
    - The first component is latitude with a sign (+ or -).
    - The second component is longitude with a sign (+ or -).
    - The third component is height with a sign (+ or -).
    - The Coordinated Reference System (CRS) is optional (e.g. CRSWGS_84);
        this contravenes the specification but matches actual practice.
    - There may or may not be a trailing slash.

    Args:
        iso_6709_str: The ISO 6709 string to parse.

    Returns:
        A tuple containing the latitude and longitude as floats, the height as a float or None, and the CRS as a string or None.

    Raises:
        ValueError: If the string is not a valid ISO 6709 string.
    """
    pattern = re.compile(
        r"""
        ^  # Start of string
        (?P<latitude>[+-]\d+(?:\.\d+)?)  # Latitude with sign and optional decimal
        (?P<longitude>[+-]\d+(?:\.\d+)?)  # Longitude with sign and optional decimal
        (?:  # Optional height and CRS group
            (?P<height>[+-]?\d+(?:\.\d+)?)  # Height with sign and optional decimal
            # (?:CRS(?P<crs>[^/]+))?  # Optional CRS (string beginning with CRS), only if height is present
            (?:CRS(?P<crs>.*?(?=\/|$)))?  # Optional CRS (string beginning with CRS), only if height is present
        )?
        /?  # Optional trailing "/"
        $  # End of string
    """,
        re.VERBOSE,
    )

    match = pattern.match(iso_6709_str)
    if match:
        latitude = float(match.group("latitude"))
        longitude = float(match.group("longitude"))
        height = float(match.group("height")) if match.group("height") else None
        crs = match.group("crs") if match.group("crs") else None
        if crs and not height:
            raise ValueError(f"CRS cannot be present without height: {iso_6709_str}")
        return latitude, longitude, height, crs
    else:
        raise ValueError(f"Invalid ISO 6709 location string: {iso_6709_str}")

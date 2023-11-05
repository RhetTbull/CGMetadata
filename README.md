# CGMetadata

Read and write image metadata on macOS from Python using the native [ImageIO / Core Graphics frameworks](https://developer.apple.com/documentation/imageio).

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO. Writing is not currently supported for RAW file formats.

Video formats are not currently supported.

## Synopsis

```pycon
>>> from cgmetadata import ImageMetadata
>>> md = ImageMetadata("tests/data/test.heic")
>>> md.exif["LensMake"]
'Apple'
>>> md.iptc["Keywords"]
(
    flower,
    plant,
    farm
)
>>> md.xmp["dc:description"]
['A sunflower plant']
>>> # write an XMP sidecar file for the image
>>> with open("test.xmp", "w") as f:
...     md.xmp_dump(f)
...
```

## Installation

```bash
pip install cgmetadata
```

## Usage

```python
...
```

## CLI

```bash
...
```

## API Reference

```python
...
```

## Supported Versions

CGMetadata has been tested on macOS 13 (Ventura) but should work on macOS 11 (Big Sur) and later. It will not work on earlier versions of macOS due to the use of certain APIs that were introduced in macOS 11. It is compatible with Python 3.9 and later.

## License

MIT License, copyright Rhet Turnbull, 2023.

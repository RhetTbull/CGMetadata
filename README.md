# CGMetadata

Read and write image metadata on macOS from Python using the native ImageIO / Core Graphics frameworks.

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO. Writing is not currently supported for RAW file formats.

Video formats are not currently supported.

>*Note*: This is a work in progress and not yet ready for use.

## Synopsis

```pycon
>>> from cgmetadata import ImageMetadata
>>> md = ImageMetadata("IMG_1997.HEIC")
>>> md.properties
...
>>> md.exif
...
>>> md.xmp
...
>>> # write an XMP sidecar file
>>> with open("IMG_1997.xmp", "w") as fd:
...     md.xmp_dump(fd)
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

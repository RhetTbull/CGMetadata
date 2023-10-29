# CGMetadata

Read and write image metadata on macOS from Python using the native ImageIO / Core Graphics frameworks.

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO. Writing is not currently supported for RAW file formats.

Video formats are not currently supported.

## Synopsis

```pycon
>>> from cgmetadata import ImageMetadata
>>> md = ImageMetadata("IMG_1997.HEIC")
>>> md.properties
...
>>> md.metadata
...
>>> md.xmp
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

## License

MIT License, copyright Rhet Turnbull, 2023.

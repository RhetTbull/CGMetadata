# CGMetadata

Read and write image metadata on macOS from Python using the native [ImageIO / Core Graphics frameworks](https://developer.apple.com/documentation/imageio).

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO.

Writing is not currently supported for RAW file formats.  Writing of metadata has been tested on JPEG, PNG, TIFF, and HEIC files however it should be considered experimental. If you are using CGMetadata to write metadata to image files, please make sure you have tested the results before using it in production.

Video formats are not currently supported.

## Synopsis

<!--
Setup for doctest:

```pycon
>>> import shutil
>>> import os
>>> try:
...     os.remove("test.jpeg")
... except Exception:
...     pass
...
>>> try:
...     os.remove("test.xmp")
... except Exception:
...     pass
...
>>>  
>>> cwd = os.getcwd()
>>> _ = shutil.copy("tests/data/test.jpeg", os.path.join(cwd, "test.jpeg"))
>>> 
```
-->

```pycon
>>> from cgmetadata import ImageMetadata, IPTC, XMP
>>> md = ImageMetadata("test.jpeg")
>>> md.exif["LensMake"]
'Apple'
>>> md.iptc["Keywords"]
['fruit', 'tree']
>>> md.xmp["dc:description"]
['A pair of pears on a tree']
>>> # get XMP sidecar as a str
>>> xmp = md.xmp_dumps()
>>> # write an XMP sidecar file for the image
>>> with open("test.xmp", "w") as f:
...     md.xmp_dump(f)
...
>>> # read metadata from  XMP sidecar file and apply to image
>>> with open("test.xmp", "r") as f:
...     md.xmp_load(f)
...
>>> 
>>> md.write()
>>> # set metadata
>>> md.set(XMP, "dc:description", ["Test image"])
>>> md.set(IPTC, "Keywords", ["foo", "bar"])
>>> md.write()
>>> md.xmp["dc:description"]
['Test image']
>>> md.iptc["Keywords"]
['foo', 'bar']
>>> 
>>> # update values with context manager
>>> with ImageMetadata("test.jpeg") as md:
...     md.set(IPTC, "Keywords", ["Fizz", "Buzz"])
...     md.set(XMP, "dc:creator", ["CGMetadata"])
...
>>> md.iptc["Keywords"]
['Fizz', 'Buzz']
>>> 
```

## Installation

```bash
pip install cgmetadata
```

## Documentation

The documentation for CGMetadata is available at [https://RhetTbull.github.io/CGMetadata/](https://RhetTbull.github.io/CGMetadata/).

## Source Code

The source code for this project is available on [GitHub](https://github.com/RhetTbull/CGMetadata).

## Command Line Interface

The package will install a small command line utility, `cgmd`, which prints
metadata for an image file in tabular, JSON, CSV, or TSV formats.

```
usage: cgmd [-h] [--version] [--csv] [--tsv] [--json] [--indent INDENT] IMAGE

Print metadata for image files in various formats.

positional arguments:
  IMAGE                 path to image file

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --csv, -c             output as comma separated values (CSV)
  --tsv, -t             output as tab separated values (TSV)
  --json, -j            output as JSON
  --indent INDENT, -i INDENT
                        indent level for JSON; default 4, use 0 for no indentation
```

## Supported Versions

CGMetadata has been tested on macOS 13 (Ventura) but should work on macOS 11 (Big Sur) and later. It will not work on earlier versions of macOS due to the use of certain APIs that were introduced in macOS 11. It is compatible with Python 3.9 and later.

## License

MIT License, copyright Rhet Turnbull, 2023.

<!--
Cleanup for doctest:

```pycon
>>> import os
>>> os.remove("test.jpeg")
>>> os.remove("test.xmp")
>>> 
```
-->
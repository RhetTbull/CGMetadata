# CGMetadata

Read and write image metadata on macOS from Python using the native [ImageIO / Core Graphics frameworks](https://developer.apple.com/documentation/imageio).

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO. Reading is also supported for video formats using AVFoundation.

Writing is not currently supported for RAW file formats nor for video formats.  Writing of metadata has been tested on JPEG, PNG, TIFF, and HEIC files however it should be considered experimental. If you are using CGMetadata to write metadata to image files, please make sure you have tested the results before using it in production.

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
>>> try:
...     os.remove("test.MOV")
... except Exception:
...     pass
...
>>>  
>>> cwd = os.getcwd()
>>> _ = shutil.copy("tests/data/test.jpeg", os.path.join(cwd, "test.jpeg"))
>>> 
>>> _ = shutil.copy("tests/data/test.MOV", os.path.join(cwd, "test.MOV"))
>>> 
```
-->

```pycon
>>> from cgmetadata import ImageMetadata, VideoMetadata, IPTC, XMP
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
>>> # read metadata from video file
>>> md = VideoMetadata("test.MOV")
>>> md.xmp.get("dc:subject")
['Coffee', 'Espresso']
>>> 
```

CGMetadata also include a utility function for reading an XMP file and returning a dictionary of metadata using native macOS APIs. This may be useful by itself as it doesn't require the use of external libraries or XML parsers.

<!--
Setup for doctest:

```pycon
>>> import shutil
>>> import os
>>> try:
...     os.remove("test.xmp")
... except Exception:
...     pass
...
>>>  
>>> cwd = os.getcwd()
>>> _ = shutil.copy("tests/data/test.MOV.xmp", os.path.join(cwd, "test.xmp"))
>>> 
```
-->

```pycon
>>> from cgmetadata import metadata_dictionary_from_xmp_packet
>>> xmp_data = open("test.xmp").read()
>>> metadata_dictionary_from_xmp_packet(xmp_data)
{'dc:subject': ['Coffee', 'Espresso'], 'iio:hasXMP': 'True'}
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

The package will install a small command line interface (CLI), `cgmd`, which prints
metadata for an image file in tabular, JSON, CSV, TSV, or XMP formats. The CLI can also
be run by executing `python3 -m cgmetadata`.

```
usage: cgmd [-h] [--version] [--csv] [--tsv] [--json] [--xmp] [--indent INDENT] [--no-header] IMAGE_OR_VIDEO

Print metadata for image files in various formats.

positional arguments:
  IMAGE_OR_VIDEO        path to image or video file

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --csv, -c             output as comma separated values (CSV); see also --no-header
  --tsv, -t             output as tab separated values (TSV); see also --no-header
  --json, -j            output as JSON; see also --indent
  --xmp, -x             output XMP sidecar for image; see also --no-header
  --indent INDENT, -i INDENT
                        indent level for JSON; default 4, use 0 for no indentation
  --no-header, -H       when used with --csv, --tsv, omit column headers; when used with --xmp, omit XMP packet header
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
>>> os.remove("test.MOV")
>>> 
```
-->
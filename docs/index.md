# Welcome to CGMetadata's Documentation

Read and write image metadata on macOS from Python using the native [ImageIO / Core Graphics frameworks](https://developer.apple.com/documentation/imageio).

CGMetadata is a Python wrapper around the macOS ImageIO and Core Graphics frameworks. It provides a simple interface for reading and writing image metadata, including EXIF, IPTC, and XMP data. Reading is supported for all image formats supported by ImageIO.

Writing is not currently supported for RAW file formats.  Writing of metadata has been tested on JPEG, PNG, TIFF, and HEIC files however it should be considered experimental. If you are using CGMetadata to write metadata to image files, please make sure you have tested the results before using it in production.

Video formats are not currently supported.

## Source Code

The source code for this project is available on [GitHub](https://github.com/RhetTbull/CGMetadata).

## Installation

or via pip:

```bash
    pip3 install cgmetadata 
```

## License

CGMetadata is published under the [MIT license](https://mit-license.org/), Copyright (c) 2023, Rhet Turnbull.

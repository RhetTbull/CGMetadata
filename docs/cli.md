# Command Line Interface

The package will install a small command line utility, `cgmd`, which prints
metadata for an image file in tabular, JSON, CSV, TSV, or XMP formats.
The CLI can also be used by executing `python3 -m cgmetadata`.

```
usage: cgmd [-h] [--version] [--csv] [--tsv] [--json] [--xmp] [--indent INDENT] [--no-header] IMAGE_OR_VIDEO

Print metadata for image and video files in various formats.

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

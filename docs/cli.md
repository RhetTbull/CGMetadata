# Command Line Interface

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

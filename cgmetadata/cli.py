"""CLI for CGMetadata. """

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from typing import Any

from rich import print
from rich.console import Console
from rich.table import Table

from ._version import __version__
from .classes import ImageMetadata, VideoMetadata
from .utils import is_image, is_video


def main():
    """Print metadata for image and video files."""
    arg_parser = argparse.ArgumentParser(
        description="Print metadata for image and video files in various formats."
    )
    arg_parser.add_argument(
        "image", metavar="IMAGE_OR_VIDEO", help="path to image or video file"
    )
    arg_parser.add_argument(
        "--version", "-v", action="version", version="%(prog)s " + __version__
    )
    arg_parser.add_argument(
        "--csv",
        "-c",
        action="store_true",
        help="output as comma separated values (CSV); see also --no-header",
    )
    arg_parser.add_argument(
        "--tsv",
        "-t",
        action="store_true",
        help="output as tab separated values (TSV); see also --no-header",
    )
    arg_parser.add_argument(
        "--json", "-j", action="store_true", help="output as JSON; see also --indent"
    )
    arg_parser.add_argument(
        "--xmp",
        "-x",
        action="store_true",
        help="output XMP sidecar for image; see also --no-header",
    )
    arg_parser.add_argument(
        "--indent",
        "-i",
        type=int,
        help="indent level for JSON; default 4, use 0 for no indentation",
        default=4,
    )
    arg_parser.add_argument(
        "--no-header",
        "-H",
        action="store_true",
        help="when used with --csv, --tsv, omit column headers; "
        "when used with --xmp, omit XMP packet header",
    )
    args = arg_parser.parse_args()

    # argument validation
    if not pathlib.Path(args.image).exists():
        print(f"File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    if not (is_image(args.image) or is_video(args.image)):
        print(f"Not an image or video file: {args.image}", file=sys.stderr)
        sys.exit(1)
    if sum([args.csv, args.tsv, args.json, args.xmp]) > 1:
        print(
            "Only one of --csv, --tsv, --json, --xmp can be specified", file=sys.stderr
        )
        sys.exit(1)

    # load metadata and print in the appropriate format
    if is_image(args.image):
        md = ImageMetadata(args.image)
    else:
        md = VideoMetadata(args.image)
    dict_data = md.asdict()

    if args.json:
        indent = args.indent or None
        json_str = md_dict_to_json(dict_data, indent)
        print(json_str)
        sys.exit(0)

    if args.csv:
        print_csv(dict_data, header=not args.no_header)
        sys.exit(0)

    if args.tsv:
        print_csv(dict_data, delim="\t", header=not args.no_header)
        sys.exit(0)

    if args.xmp:
        print(md.xmp_dumps(header=not args.no_header))
        sys.exit(0)

    # default output
    print_md_dict(dict_data, args.image)
    sys.exit(0)  # always raise SystemExit for testing


def md_dict_to_json(md_dict: dict[str, Any], indent: int = 4) -> str:
    """Convert a dictionary of metadata to a JSON string."""

    def default(o):
        if isinstance(o, bytes):
            return format_bytes(o)
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )

    return json.dumps(md_dict, default=default, indent=indent)


def format_bytes(b: bytes) -> str:
    """Format bytes as a string for pretty printing."""
    length = len(b)
    first = min(length, 16)
    first_bytes = b[:first].hex()
    value = f"<{length} bytes: {first_bytes}"
    if length > first:
        value += "..."
    value += ">"
    return value


def format_value(value: Any) -> Any:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, bytes):
        return format_bytes(value)
    return str(value)


def flatten_metadata_dict(
    d: dict[str, Any], group_key: str = "", parent_key: str = ""
) -> list[tuple[str, str, Any]]:
    """Flatten metadata dictionary into a list of tuples of (group, tag, value)"""
    items = []
    for k, v in d.items():
        if parent_key:
            new_key = f"{parent_key}.{k}"
        else:
            new_key = k
        if isinstance(v, dict):
            if group_key:
                items.extend(flatten_metadata_dict(v, group_key, new_key))
            else:
                items.extend(flatten_metadata_dict(v, new_key))
        else:
            items.append((group_key, new_key, v))
    return items


def print_md_dict(md_dict: dict[str, Any], filename: str):
    """Print metadata dictionary."""

    items = sorted(flatten_metadata_dict(md_dict))
    table = Table(title=f"Metadata for {filename}")
    table.add_column("Group")
    table.add_column("Tag")
    table.add_column("Value")
    for group, tag, value in items:
        group = group or "None"
        table.add_row(group, tag, format_value(value))
        # items_to_print.append((group, tag, format_value(value)))
        # print(f"{group} : {tag} : {format_value(value)}")
    console = Console()
    console.print(table)


def print_csv(md_dict: dict[str, Any], delim: str = ",", header: bool = True):
    """Print metadata dictionary as CSV.

    Args:
        md_dict: metadata dictionary
        delim: delimiter to use
        header: if True, print header row
    """

    items = sorted(flatten_metadata_dict(md_dict))
    items_to_print = []
    for group, tag, value in items:
        group = group or "None"
        items_to_print.append((group, tag, format_value(value)))

    csv_writer = csv.writer(sys.stdout, delimiter=delim)
    if header:
        csv_writer.writerow(["Group", "Tag", "Value"])
    csv_writer.writerows(items_to_print)


if __name__ == "__main__":
    main()

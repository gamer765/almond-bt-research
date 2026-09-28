#!/usr/bin/env python3
"""List RAR members and metadata without extracting the firmware."""

from __future__ import annotations

import argparse
from pathlib import Path

import rarfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "archive",
        type=Path,
        help="First volume of a RAR/multipart RAR archive",
    )
    args = parser.parse_args()

    with rarfile.RarFile(args.archive) as archive:
        print(f"archive: {args.archive}")
        for member in archive.infolist():
            print(member.filename)
            print(f"  size:       {member.file_size}")
            print(f"  compressed: {member.compress_size}")
            print(f"  directory:  {member.isdir()}")


if __name__ == "__main__":
    main()

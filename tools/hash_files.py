#!/usr/bin/env python3
"""Calculate MD5 and SHA-256 without loading large firmware files into RAM."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path, chunk_size: int = 8 * 1024 * 1024) -> tuple[str, str]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()

    for path in args.files:
        md5, sha256 = digest(path)
        print(f"{path}")
        print(f"  size:   {path.stat().st_size}")
        print(f"  md5:    {md5}")
        print(f"  sha256: {sha256}")


if __name__ == "__main__":
    main()

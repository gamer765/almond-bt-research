#!/usr/bin/env python3
"""Generate a Markdown package-directory inventory from reconstructed images."""

from __future__ import annotations

import argparse
from pathlib import Path

from ext4_reader import Ext4


LOCATIONS = {
    "system": ["/system/app", "/system/priv-app"],
    "product": ["/app", "/priv-app"],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image_dir", type=Path, help="Directory containing system.img/product.img")
    args = parser.parse_args()

    print("# Package directory inventory\n")
    print(
        "Directory/file names from reconstructed filesystems; these are not necessarily "
        "Android manifest package IDs.\n"
    )

    for partition, directories in LOCATIONS.items():
        fs = Ext4(args.image_dir / f"{partition}.img")
        try:
            for directory in directories:
                try:
                    names = sorted(name for name, _, _ in fs.listdir(directory))
                except FileNotFoundError:
                    continue
                print(f"## {partition}:{directory} — {len(names)} entries\n")
                for name in names:
                    print(f"- `{name}`")
                print()
        finally:
            fs.close()


if __name__ == "__main__":
    main()

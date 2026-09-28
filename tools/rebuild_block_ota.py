#!/usr/bin/env python3
"""Reconstruct Android block-OTA *.new.dat.br partitions directly from an OTA ZIP."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import brotli

BLOCK_SIZE = 4096


def parse_ranges(spec: str) -> list[tuple[int, int]]:
    nums = [int(x) for x in spec.split(",")]
    count, values = nums[0], nums[1:]
    if count != len(values) or count % 2:
        raise ValueError(f"bad range set: {spec}")
    return list(zip(values[0::2], values[1::2]))


def parse_transfer(text: str):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    version = int(lines[0])
    declared_new_blocks = int(lines[1])
    commands = []
    max_block = 0
    counted_new_blocks = 0

    for line in lines[4:]:
        op, spec = line.split(" ", 1)
        ranges = parse_ranges(spec)
        for start, end in ranges:
            max_block = max(max_block, end)
            if op == "new":
                counted_new_blocks += end - start
        commands.append((op, ranges))

    return version, declared_new_blocks, commands, max_block, counted_new_blocks


def rebuild(ota: zipfile.ZipFile, partition: str, output: Path) -> None:
    transfer = ota.read(f"{partition}.transfer.list").decode()
    version, declared, commands, max_block, counted = parse_transfer(transfer)
    new_ranges = [r for op, ranges in commands if op == "new" for r in ranges]

    decompressor = brotli.Decompressor()
    range_index = 0
    range_offset = 0
    produced = 0

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as dst:
        # This is intentionally sparse. Transfer lists may address erased blocks
        # beyond the filesystem's own superblock size.
        dst.truncate(max_block * BLOCK_SIZE)

        def consume(data: bytes) -> None:
            nonlocal range_index, range_offset, produced
            view = memoryview(data)
            source_offset = 0
            while source_offset < len(view):
                if range_index >= len(new_ranges):
                    raise RuntimeError("decompressed stream is larger than transfer-list new ranges")
                start, end = new_ranges[range_index]
                range_bytes = (end - start) * BLOCK_SIZE
                remaining = range_bytes - range_offset
                length = min(remaining, len(view) - source_offset)
                dst.seek(start * BLOCK_SIZE + range_offset)
                dst.write(view[source_offset : source_offset + length])
                source_offset += length
                range_offset += length
                produced += length
                if range_offset == range_bytes:
                    range_index += 1
                    range_offset = 0

        with ota.open(f"{partition}.new.dat.br") as src:
            while chunk := src.read(4 * 1024 * 1024):
                decoded = decompressor.process(chunk)
                if decoded:
                    consume(decoded)

    expected = counted * BLOCK_SIZE
    if produced != expected:
        raise RuntimeError(f"{partition}: produced {produced} bytes, expected {expected}")

    print(
        f"{partition}: transfer-v{version}, declared_new={declared}, "
        f"new_blocks={counted}, envelope={max_block * BLOCK_SIZE}, output={output}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ota", type=Path)
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("out"))
    parser.add_argument(
        "-p",
        "--partitions",
        nargs="+",
        default=["system", "vendor", "product", "tvconfig", "odm"],
    )
    args = parser.parse_args()

    with zipfile.ZipFile(args.ota) as ota:
        for partition in args.partitions:
            rebuild(ota, partition, args.output_dir / f"{partition}.img")


if __name__ == "__main__":
    main()

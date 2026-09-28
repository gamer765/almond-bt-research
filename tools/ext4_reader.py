#!/usr/bin/env python3
"""Small read-only ext4 reader used for firmware analysis without mounting images.

Supports extent-based regular files, directories and inline symlinks. It is intentionally
minimal: enough to inspect Android OTA images in an unprivileged environment.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


class Ext4:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.f = self.path.open("rb")
        self.f.seek(1024)
        sb = self.f.read(1024)
        if struct.unpack_from("<H", sb, 56)[0] != 0xEF53:
            raise ValueError(f"{path}: not an ext filesystem")

        self.inodes_count = struct.unpack_from("<I", sb, 0)[0]
        self.blocks_count = struct.unpack_from("<I", sb, 4)[0]
        self.block_size = 1024 << struct.unpack_from("<I", sb, 24)[0]
        self.blocks_per_group = struct.unpack_from("<I", sb, 32)[0]
        self.inodes_per_group = struct.unpack_from("<I", sb, 40)[0]
        self.inode_size = struct.unpack_from("<H", sb, 88)[0] or 128
        self.feature_incompat = struct.unpack_from("<I", sb, 96)[0]
        self.desc_size = (
            struct.unpack_from("<H", sb, 254)[0]
            if self.feature_incompat & 0x80
            else 32
        )
        self.desc_size = max(self.desc_size, 32)
        self.gdt_offset = 2 * self.block_size if self.block_size == 1024 else self.block_size

    def close(self):
        self.f.close()

    def read_at(self, offset: int, length: int) -> bytes:
        self.f.seek(offset)
        return self.f.read(length)

    def inode_table_block(self, group: int) -> int:
        d = self.read_at(self.gdt_offset + group * self.desc_size, self.desc_size)
        lo = struct.unpack_from("<I", d, 8)[0]
        hi = struct.unpack_from("<I", d, 40)[0] if self.desc_size >= 64 else 0
        return lo | (hi << 32)

    def inode(self, ino: int):
        group = (ino - 1) // self.inodes_per_group
        index = (ino - 1) % self.inodes_per_group
        table = self.inode_table_block(group)
        raw = self.read_at(
            table * self.block_size + index * self.inode_size, self.inode_size
        )
        mode = struct.unpack_from("<H", raw, 0)[0]
        size_lo = struct.unpack_from("<I", raw, 4)[0]
        flags = struct.unpack_from("<I", raw, 32)[0]
        size_hi = struct.unpack_from("<I", raw, 108)[0] if len(raw) >= 112 else 0
        size = size_lo | (size_hi << 32) if (mode & 0xF000) == 0x8000 else size_lo
        return {"ino": ino, "mode": mode, "size": size, "flags": flags, "block": raw[40:100]}

    def extents(self, inode):
        result = []

        def walk(node: bytes):
            magic, entries, _, depth, _ = struct.unpack_from("<HHHHI", node, 0)
            if magic != 0xF30A:
                raise ValueError("inode does not contain an ext4 extent tree")

            if depth == 0:
                for i in range(entries):
                    off = 12 + i * 12
                    logical, length, start_hi, start_lo = struct.unpack_from(
                        "<IHHI", node, off
                    )
                    unwritten = bool(length & 0x8000)
                    length &= 0x7FFF
                    result.append(
                        (logical, length, (start_hi << 32) | start_lo, unwritten)
                    )
            else:
                for i in range(entries):
                    off = 12 + i * 12
                    _, leaf_lo, leaf_hi, _ = struct.unpack_from("<IIHH", node, off)
                    leaf = (leaf_hi << 32) | leaf_lo
                    walk(self.read_at(leaf * self.block_size, self.block_size))

        walk(inode["block"])
        return sorted(result)

    def read_inode(self, ino: int) -> bytes:
        inode = self.inode(ino)
        size = inode["size"]

        # Small symlinks are stored directly inside i_block.
        if (inode["mode"] & 0xF000) == 0xA000 and size <= 60:
            return bytes(inode["block"][:size])

        EXT4_EXTENTS_FL = 0x80000
        if not inode["flags"] & EXT4_EXTENTS_FL:
            raise NotImplementedError(
                f"inode {ino}: only extent-based files are supported"
            )

        data = bytearray(size)
        for logical, length, physical, unwritten in self.extents(inode):
            start = logical * self.block_size
            count = min(length * self.block_size, max(0, size - start))
            if count > 0 and not unwritten:
                data[start : start + count] = self.read_at(
                    physical * self.block_size, count
                )
        return bytes(data)

    def dir_entries(self, ino: int):
        data = self.read_inode(ino)
        pos = 0
        entries = []
        while pos + 8 <= len(data):
            child, rec_len, name_len, file_type = struct.unpack_from("<IHBB", data, pos)
            if rec_len < 8 or pos + rec_len > len(data):
                break
            if child and name_len:
                name = data[pos + 8 : pos + 8 + name_len].decode(
                    "utf-8", "surrogateescape"
                )
                if name not in (".", ".."):
                    entries.append((name, child, file_type))
            pos += rec_len
        return entries

    def lookup(self, path: str) -> int:
        ino = 2
        for component in [x for x in path.strip("/").split("/") if x]:
            entries = {name: child for name, child, _ in self.dir_entries(ino)}
            if component not in entries:
                raise FileNotFoundError(path)
            ino = entries[component]
        return ino

    def listdir(self, path: str = "/"):
        return self.dir_entries(2 if path == "/" else self.lookup(path))

    def cat(self, path: str) -> bytes:
        return self.read_inode(self.lookup(path))

    def walk(self, path: str = "/"):
        start = 2 if path == "/" else self.lookup(path)

        def recurse(base: str, ino: int):
            for name, child, file_type in self.dir_entries(ino):
                full = base.rstrip("/") + "/" + name if base != "/" else "/" + name
                meta = self.inode(child)
                yield full, child, file_type, meta
                if file_type == 2:
                    yield from recurse(full, child)

        yield from recurse(path, start)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("command", choices=["ls", "cat", "walk"])
    parser.add_argument("path", nargs="?", default="/")
    args = parser.parse_args()

    fs = Ext4(args.image)
    try:
        if args.command == "ls":
            for name, ino, file_type in fs.listdir(args.path):
                meta = fs.inode(ino)
                print(
                    f"{ino:8d} type={file_type} mode={meta['mode']:06o} "
                    f"size={meta['size']:10d} {name}"
                )
        elif args.command == "cat":
            import sys

            sys.stdout.buffer.write(fs.cat(args.path))
        else:
            for path, ino, file_type, meta in fs.walk(args.path):
                print(
                    f"{ino:8d} type={file_type} mode={meta['mode']:06o} "
                    f"size={meta['size']:10d} {path}"
                )
    finally:
        fs.close()


if __name__ == "__main__":
    main()

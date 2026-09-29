#!/usr/bin/env python3
"""Static verifier for the Almond PS7715 GhostLock profile.

This does not execute the exploit. It verifies the profile's kernel anchors
against a decompressed Almond kernel image.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

CRITICAL_ANCHORS = (
    ("address.init_task", 0x500),
    ("address.pi_task", 64),
    ("address.ashmem_fops", 64),
    ("address.ashmem_misc_fops", 64),
    ("address.ashmem_open", 128),
    ("address.ashmem_release", 128),
    ("address.ashmem_ioctl", 128),
    ("address.ashmem_mmap", 128),
    ("address.configfs_read_file", 128),
    ("address.configfs_write_file", 128),
)


def parse_profile(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError(f"malformed line: {raw}")
        values[key.strip()] = value.strip()
    return values


def u32(data: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(data):
        raise ValueError(f"read outside kernel at 0x{off:x}")
    return struct.unpack_from("<I", data, off)[0]


def addr_to_off(address: int, base: int, size: int) -> int:
    off = address - base
    if off < 0 or off >= size:
        raise ValueError(f"0x{address:08x} is outside kernel image")
    return off


def critical_digest(kernel: bytes, values: dict[str, str], base: int) -> str:
    digest = hashlib.sha256()
    for key, length in CRITICAL_ANCHORS:
        address = int(values[key], 0)
        off = addr_to_off(address, base, len(kernel))
        if off + length > len(kernel):
            raise ValueError(f"{key} range exceeds kernel image")
        digest.update(key.encode("ascii"))
        digest.update(struct.pack("<II", address, length))
        digest.update(kernel[off : off + length])
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel", type=Path, help="decompressed vmlinux.raw")
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()

    kernel = args.kernel.read_bytes()
    p = parse_profile(args.profile)
    base = int(p["analysis.kernel_image_base"], 0)
    expected_size = int(p["analysis.kernel_size"], 0)

    failures: list[str] = []
    notes: list[str] = []

    actual_sha = hashlib.sha256(kernel).hexdigest()
    if len(kernel) != expected_size:
        failures.append(f"kernel size {len(kernel)} != {expected_size}")
    if actual_sha.lower() != p["analysis.kernel_sha256"].lower():
        failures.append(f"kernel SHA-256 {actual_sha} does not match profile")

    init = int(p["address.init_task"], 0)
    tasks_off = int(p["offset.task_tasks"], 0)
    real_cred_off = int(p["offset.task_real_cred"], 0)
    cred_off = int(p["offset.task_cred"], 0)
    comm_off = int(p["offset.task_comm"], 0)
    init_off = addr_to_off(init, base, len(kernel))

    comm = kernel[init_off + comm_off : init_off + comm_off + 16].split(b"\0", 1)[0]
    if comm != b"swapper":
        failures.append(f"init_task comm is {comm!r}, expected b'swapper'")

    expected_list = init + tasks_off
    next_task = u32(kernel, init_off + tasks_off)
    prev_task = u32(kernel, init_off + tasks_off + 4)
    if next_task != expected_list or prev_task != expected_list:
        failures.append(
            f"init task list is not self-referential: "
            f"next=0x{next_task:08x} prev=0x{prev_task:08x} "
            f"expected=0x{expected_list:08x}"
        )

    real_cred = u32(kernel, init_off + real_cred_off)
    cred = u32(kernel, init_off + cred_off)
    if real_cred != cred or not (0xC0000000 <= cred < 0xFFF00000):
        failures.append(
            f"init credentials look wrong: real_cred=0x{real_cred:08x} cred=0x{cred:08x}"
        )

    fops = int(p["address.ashmem_fops"], 0)
    fops_off = addr_to_off(fops, base, len(kernel))
    slots = {
        0x24: int(p["address.ashmem_ioctl"], 0),
        0x2C: int(p["address.ashmem_mmap"], 0),
        0x30: int(p["address.ashmem_open"], 0),
        0x38: int(p["address.ashmem_release"], 0),
    }
    for slot, expected in slots.items():
        actual = u32(kernel, fops_off + slot)
        if actual != expected:
            failures.append(
                f"ashmem_fops+0x{slot:x}=0x{actual:08x}, expected 0x{expected:08x}"
            )

    misc = int(p["address.ashmem_misc_fops"], 0)
    misc_off = addr_to_off(misc, base, len(kernel))
    actual_fops = u32(kernel, misc_off)
    if actual_fops != fops:
        failures.append(
            f"ashmem misc fops slot=0x{actual_fops:08x}, expected 0x{fops:08x}"
        )

    if misc_off >= 8:
        minor = u32(kernel, misc_off - 8)
        name_ptr = u32(kernel, misc_off - 4)
        try:
            name_off = addr_to_off(name_ptr, base, len(kernel))
            name = kernel[name_off : name_off + 16].split(b"\0", 1)[0]
        except ValueError:
            name = b""
        if minor != 0xFF or name != b"ashmem":
            failures.append(
                f"miscdevice identity mismatch: minor={minor}, name={name!r}"
            )

    digest = critical_digest(kernel, p, base)
    if digest.lower() != p["analysis.critical_anchors_sha256"].lower():
        failures.append(
            "critical-anchor digest mismatch: "
            f"{digest} != {p['analysis.critical_anchors_sha256']}"
        )

    pi_task = int(p["address.pi_task"], 0)
    notes.append(
        f"pi_task candidate 0x{pi_task:08x} is included in the anchor digest "
        "but remains hardware-unverified."
    )

    if failures:
        print("FAIL")
        for item in failures:
            print(f"  - {item}")
        for item in notes:
            print(f"  note: {item}")
        return 1

    print("PASS")
    print(f"  kernel_sha256={actual_sha}")
    print(f"  critical_anchors_sha256={digest}")
    print(f"  init_task=0x{init:08x} task_struct layout verified")
    print(f"  ashmem_fops=0x{fops:08x} slots verified")
    print(f"  ashmem_misc_fops=0x{misc:08x} miscdevice link verified")
    for item in notes:
        print(f"  note: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

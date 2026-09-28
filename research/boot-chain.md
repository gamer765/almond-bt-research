# Boot-chain notes

## OTA updater behavior

The updater writes `boot.img` directly to `/dev/block/boot` and selects one of two bootloader images:

```text
if ro.boot.secure_cpu == 0:
    write images/bootloader.bin
else:
    write images/bootloader.bin.signed
```

That makes the secure/non-secure split explicit in the stock OTA logic.

## Android boot image

- page size: 2048
- kernel payload size: 7,323,800 bytes
- ramdisk: empty
- second-stage size: 136,718 bytes
- system-as-root: `ro.build.system_root_image=true`

The kernel payload is itself a legacy U-Boot uImage:

- image name: `Linux-4.9.113`
- ARM kernel
- uncompressed uImage payload
- build timestamp: 2026-07-04 01:41:13 UTC

The empty ramdisk is consistent with the root filesystem living in the system partition.

## Device trees

The second-stage payload is gzip-compressed. It expands to 540,672 bytes and begins with Amlogic's `AMLC` multi-DTB container header.

Six Flattened Device Tree magic values are present in the expanded container. Device-tree strings identify the SoC/platform as:

```text
Amlogic T5D T950D4 AM301 1.5G
```

Other strings include Cortex-A9 CPU/GIC identifiers and extensive Amlogic TV/display nodes.

## Bootloader

The unsigned bootloader contains multiple stage build identifiers, including:

```text
Built : 13:28:26, Dec  9 2021. t5d ...
Built : 13:28:57, Dec  9 2021. t5 ...
Amlogic-secure-boot-module-v0.4
```

It also contains OP-TEE/TA anti-rollback code and RPMB-related logic. Android properties report `ro.build.optee_version=3.13`.

## dm-verity

The boot cmdline contains:

```text
veritykeyid=id:f3530e18f64d11fc25eb2dd762979f078de990bf
```

The system filesystem contains `/verity_key`, and stock fstab marks system and vendor as `verify`. This build therefore still has a verified-partition chain even though Amazon's developer/root-capable userspace paths are present.

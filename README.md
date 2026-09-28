# almond-bt research

Reverse-engineering workspace for the Amazon/Insignia Fire TV **almond-bt** platform.

The current baseline is the full Fire OS **7.7.1.5 / PS7715 user 5585** OTA.

## Current firmware

- OTA: `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin`
- Size: **745,467,062 bytes**
- MD5: `44451b108c3778e4b6c9d3a1dedcb450`
- SHA-256: `f8e88ef3012dca2c0e5f1ff68198d1ebcf97d8b51a307d15e3c561c219102dd9`
- Fire OS: **7.7.1.5 (PS7715.5585N/5585)**
- Android: **9 / API 28**
- Security patch: **2026-03-01**
- SoC/platform identified from DTB: **Amlogic T5D / T950D4, ARM 32-bit**
- Kernel: **Linux 4.9.113**

## What has been completed

The uploaded multipart archive has been extracted and the stock OTA analyzed.

- Reconstructed `system`, `vendor`, `product`, `tvconfig`, and `odm`
- Recorded SHA-256 hashes for all reconstructed filesystems
- Parsed stock updater logic and dm-verity configuration
- Unpacked the Android boot image and Amlogic multi-DTB second stage
- Identified secure/non-secure bootloader OTA paths
- Inventoried system/product application directories
- Inspected SELinux policy variants
- Disassembled Amazon-specific `adbd` debug/root logic

A significant finding is that the shipping `adbd` contains an Amazon engineering root path gated by trusted boot state plus IDME flags. See **[security-debug-paths.md](research/security-debug-paths.md)** for the exact predicates recovered from the ARM binary.

## Key research

- [PS7715 baseline](research/ps7715-baseline.md)
- [Amazon debug/root paths](research/security-debug-paths.md)
- [Boot chain](research/boot-chain.md)
- [Package inventory](research/package-inventory.md)
- [Archive metadata](docs/archive-metadata.md)
- [Firmware inventory](docs/firmware-inventory.md)

## Tools

### Reconstruct block-OTA partitions

```bash
python -m pip install -r requirements.txt
python tools/rebuild_block_ota.py update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin -o out
```

### Browse a reconstructed filesystem without mounting it

```bash
python tools/ext4_reader.py out/system.img ls /
python tools/ext4_reader.py out/system.img ls /system/priv-app
python tools/ext4_reader.py out/vendor.img cat /etc/fstab.amlogic
```

### Generate package-directory inventory

```bash
python tools/package_inventory.py out/
```

## Repository policy

Do not commit large proprietary firmware blobs or complete extracted filesystems. Keep reproducible scripts, hashes, metadata, small derived artifacts, and research notes in Git.

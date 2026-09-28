# Firmware inventory

## PS7715 / user 5585

| Field | Value |
|---|---|
| Platform | `almond-bt` |
| Fire OS build | `PS7715` |
| User build | `5585` |
| Package ID | `0035736899972` |
| Inner firmware filename | `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin` |
| Inner size from RAR header | `745,467,062` bytes |

### Uploaded multipart archive hashes

| File | Size | MD5 | SHA-256 |
|---|---:|---|---|
| `...part1.rar` | ~400 MiB | `3063fb90cb386f8284e0ca7cc2c4e543` | `1c20022c42e8485b347093a354bd86871d4d7f40ea3dff09cc7fcad99aa1c5c3` |
| `...part2.rar` | ~309 MiB | `3c8533356a5e1c1b3eadc3f1798b8c4f` | `903a7d7de41746f1fb318248a85f5cf5c8b06866365156d7f11271654c6e2801` |

These hashes identify the exact uploaded split archive used for this research. The inner `.bin` should be hashed separately after extraction.

## Next analysis passes

1. Extract the firmware image and record MD5/SHA-256.
2. Identify the outer update container format and signing metadata.
3. Inventory partitions/images and filesystem types.
4. Extract build properties, SELinux policy, init configuration, packages, kernel metadata, and boot/recovery artifacts.
5. Compare future almond-bt firmware releases against this baseline.

# Multipart archive metadata

Source archive:

- `update-kindle-almond-bt-PS7715_user_5585_0035736899972.part1.rar`
- `update-kindle-almond-bt-PS7715_user_5585_0035736899972.part2.rar`

## Volume sizes

| Volume | Bytes |
|---|---:|
| part1 | 419,430,400 |
| part2 | 323,851,835 |
| total archive bytes | 743,282,235 |

## RAR member metadata

The first RAR volume advertises a single logical member spanning the multipart archive.

| Field | Value |
|---|---|
| Member | `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin` |
| Uncompressed size | 745,467,062 bytes |
| Compressed size | 743,281,688 bytes |
| RAR compression type | 51 |
| RAR flags | 32770 |
| Member CRC32 | `d04ae492` |
| Member timestamp | `2026-09-27T19:26:25.631829959+00:00` |

This metadata was read directly from the RAR5 header with Python `rarfile`; it does not depend on successfully extracting the firmware.

## Archive checksums

### part1

- MD5: `3063fb90cb386f8284e0ca7cc2c4e543`
- SHA-256: `1c20022c42e8485b347093a354bd86871d4d7f40ea3dff09cc7fcad99aa1c5c3`

### part2

- MD5: `3c8533356a5e1c1b3eadc3f1798b8c4f`
- SHA-256: `903a7d7de41746f1fb318248a85f5cf5c8b06866365156d7f11271654c6e2801`

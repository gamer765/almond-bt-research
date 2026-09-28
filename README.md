# almond-bt research

Research workspace for the Amazon/Insignia Fire TV **almond-bt** platform, currently centered on the Fire OS 7.7.1.5 / **PS7715 user 5585** firmware package.

## Current sample

- Platform/codename: `almond-bt`
- Firmware: `PS7715_user_5585_0035736899972`
- Multipart archive:
  - `update-kindle-almond-bt-PS7715_user_5585_0035736899972.part1.rar`
  - `update-kindle-almond-bt-PS7715_user_5585_0035736899972.part2.rar`
- RAR header reports one inner file:
  - `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin`
  - uncompressed size: **745,467,062 bytes**

The firmware binary itself is intentionally not committed here. This repo stores reproducible tooling, hashes, notes, extracted metadata, diffs, and research artifacts.

## Layout

- `docs/` — firmware inventory and research notes
- `tools/` — local inspection and hashing utilities
- `research/` — findings derived from firmware analysis

## Quick start

```bash
python -m pip install -r requirements.txt
python tools/inspect_rar.py /path/to/update-kindle-almond-bt-PS7715_user_5585_0035736899972.part1.rar
python tools/hash_files.py /path/to/update-kindle-almond-bt-PS7715_user_5585_0035736899972.part*.rar
```

## Ground rules

Keep large vendor firmware images and extracted proprietary blobs out of Git. Prefer metadata, hashes, scripts, manifests, small patches/diffs, and documentation that make the analysis reproducible.

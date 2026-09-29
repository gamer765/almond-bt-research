# Almond PS7715 GhostLock relocation notes

## Firmware identity

- OTA: `update-kindle-almond-bt-PS7715_user_5585_0035736899972.bin`
- MD5: `44451b108c3778e4b6c9d3a1dedcb450`
- SHA-256: `f8e88ef3012dca2c0e5f1ff68198d1ebcf97d8b51a307d15e3c561c219102dd9`
- Product: `almond`
- Variant: `almond-bt`
- Fingerprint: `Amazon/almond/almond:9/PS7715.5585N/0035736899840:user/amz-p,release-keys`
- Incremental: `0035736899972`
- Kernel: `4.9.113`, ARMv7
- Kernel image base: `0xc0108000`
- Decompressed kernel size: `18886656`
- Kernel SHA-256: `c0c47bc75e874fdb623fe13d570c32920b6c4dcc3eb4420985720fe74e3ae176`
- IKCONFIG SHA-256: `af0d3ca1fa95e56aef15c863fa4c1417c58a9ef99f0136c31ab84aad136912e7`
- Boot SHA-256: `34611d2c52b01061a320c1ccef44e7a6d19dfdf14edecfcf9df50dde8b45673a`
- Second-stage SHA-256: `285fc7429b5d0a006ef3c97d6eb488cf462ada20af03769ebef34db6cda7898a`

Kernel build string:

`Linux version 4.9.113-g6900cba992d3-dirty (build@de51a440f364) (gcc version 6.3.1 20170109 (Linaro GCC 6.3-2017.02) ) #1 SMP PREEMPT Sat Jul 4 01:41:10 UTC 2026`

## Reference choice

The public GhostLock 5.10 tree targets newer Linux 5.10 Fire TV devices.
Almond is a 32-bit ARM Fire OS 7 platform on Linux 4.9.113, so the closer
reference implementation is the profile-driven ARM32 Hazel port of the same
CVE-2026-43499 family.

## init_task and task_struct

Static `swapper` recovery places Almond `init_task` at
`0xc120d540`.

Checks at that base:

- `init_task + 0x3f4` is the `swapper` comm string.
- `init_task + 0x258` contains a self-referential task list; both pointers
  resolve to `0xc120d798`.
- `init_task + 0x3ec` and `+0x3f0` are equal kernel pointers to the init
  credentials.

Therefore:

```
offset.task_tasks=0x258
offset.task_real_cred=0x3ec
offset.task_cred=0x3f0
offset.task_comm=0x3f4
```

## Ashmem relocation

Recovered and cross-linked functions:

```
ashmem_release = 0xc07757b4
ashmem_open    = 0xc0775918
ashmem_mmap    = 0xc07759a4
ashmem_ioctl   = 0xc0775f88
ashmem_fops    = 0xc0d464c8
ashmem_misc_fops = 0xc1257df4
```

The file_operations table contains the expected ARM32 slots:

```
+0x24 ioctl   -> 0xc0775f88
+0x2c mmap    -> 0xc07759a4
+0x30 open    -> 0xc0775918
+0x38 release -> 0xc07757b4
```

The writable miscdevice slot is independently identified by the neighboring
minor value `255` and the `ashmem` device-name pointer.

## Configfs relocation

The configfs routines were matched to Linux 4.9 `fs/configfs/file.c`
semantics.

```
configfs_write_file = 0xc040f4e0
configfs_read_file  = 0xc040f67c
```

## pi_task caveat

Hazel profiles in this Linux 4.9 family retain a stable static-data relationship
of `pi_task = init_task - 0x234`. Applying that relationship after relocating
Almond `init_task` gives the current candidate:

`pi_task = 0xc120d30c`

This is the one target field that still needs device-side validation before the
port can be called hardware-tested.

## Critical-anchor digest

Using the reference profile creator's anchor order and byte lengths:

`dcdf81697e8b4931d16e02b8fee654e4ba69d712e242e327cba3ce1208ca431b`

The repository verifier recomputes the digest and validates the task-list,
credential-pointer, fops, and miscdevice invariants without executing any
exploit code.

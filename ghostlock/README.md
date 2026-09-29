# GhostLock → almond-bt port status

Target firmware: Insignia F20 / Amazon `almond-bt`, Fire OS 7.7.1.5, `PS7715.5585N`, incremental `0035736899972`, Android 9 / API 28.

Upstream GhostLock branch `5.10` currently targets `sunstone` and `karat` (Fire OS 8) with device-specific kernel structure layouts and symbol offsets. The almond target must therefore be treated as a new kernel port, not as a codename-only addition.

## What can be reused

- host retry/ADB wrappers (`root.sh`, `root.ps1`)
- target registry/config mechanism
- root proof / temporary su plumbing
- much of the exploit orchestration, if almond exposes the same vulnerable futex/allocator primitives

## What must be derived for almond

1. Exact kernel release/banner and architecture from PS7715 `boot.img` or a live TV.
2. Verify the underlying CVE primitive is present in this kernel branch.
3. Kernel virtual/physical layout and KASLR assumptions.
4. `task_struct`, `cred`, waiter/PI-futex, `mm_struct`, `page`, `pipe_buffer`, and `file_operations` member offsets.
5. Symbol/function offsets used by GhostLock (`init_task`, `init_cred`, SELinux globals/hooks, kmalloc caches, ashmem fops/ioctls, pipe ops, configfs helpers, boot-id helpers, etc.).
6. Heap-groom constants (`MM_ORDER`, objects-per-slab, CPU selection, waiter stamping mode) for almond's allocator/kernel config.
7. Userspace architecture: almond advertises `armeabi-v7a`; confirm whether the primary GhostLock stage must be rebuilt as 32-bit rather than the upstream AArch64 preload + ARM32 helper arrangement.
8. Device-specific OTA package names for the Fire TV television build.

## Guarded target

`ghostlock/targets/almond/target.h` deliberately fails compilation until `ALMOND_OFFSETS_VERIFIED` is defined and real offsets are populated. This prevents accidentally running karat/sunstone values on almond.

## Live probe

Push and run `ghostlock/collect-almond.sh`:

```sh
adb push ghostlock/collect-almond.sh /data/local/tmp/
adb shell chmod 755 /data/local/tmp/collect-almond.sh
adb shell /data/local/tmp/collect-almond.sh
adb pull /sdcard/almond-ghostlock-probe.txt
```

The resulting file provides the kernel banner, ABI, kernel security/config details, ashmem/configfs presence, and any readable symbol data needed to choose the next porting path.

# `adbd` ARM reverse-engineering notes

Source binary: reconstructed `/system/bin/adbd` from PS7715/5585.

The ELF is 32-bit ARM, statically linked, Android API 28, BuildID `bef6452657ac2d302b310b736fbc54fb`, and retains local symbols.

## Exported/local symbols

```text
amzn_is_root_allowed
amzn_is_adb_auth_disable_allowed
_ZL20amzn_is_dev_unlockedv
_ZL20fos_read_debug_flagsPKc
FILE: amzn_fos_flags.cpp
```

## `amzn_is_root_allowed`

Relevant Thumb instructions:

```text
bl      amzn_is_dev_unlocked
cbz     r0, deny
...
bl      fos_read_debug_flags
tst.w   r0, #0x2
bne     allowed
...
allowed:
... klog_write(...)
movs    r0, #1
```

The string passed to `fos_read_debug_flags` resolves to `fos_flags`, and the helper prepends `/proc/idme/`.

Equivalent pseudocode:

```c
bool amzn_is_root_allowed(void) {
    if (!amzn_is_dev_unlocked())
        return false;

    uint64_t flags = fos_read_debug_flags("fos_flags");
    if ((flags & 0x2) == 0)
        return false;

    klog("amzn_fos: ADB: Auto-root succeeded");
    return true;
}
```

## `amzn_is_dev_unlocked`

The helper opens `/proc/cmdline` and performs two string searches.

First search literal:

```text
androidboot.prod=0
```

If present, it logs:

```text
amzn_fos: ADB: eng_device=%d
```

If not present, it searches again for:

```text
androidboot.unlocked_kernel=true
```

and logs:

```text
amzn_fos: ADB: unlocked_kernel=%d
```

Equivalent predicate:

```c
return strstr(cmdline, "androidboot.prod=0") != NULL ||
       strstr(cmdline, "androidboot.unlocked_kernel=true") != NULL;
```

## Root privilege drop in `adbd_main`

`adbd_main` calls `amzn_is_root_allowed`.

When it returns false, execution reaches the normal minijail setup:

```text
minijail_use_caps(...)
minijail_change_gid(..., 2000)
minijail_change_uid(..., 2000)
minijail_enter(...)
```

When Amazon root is allowed, `adbd_main` reads the property literal:

```text
service.adb.root
```

and compares it to:

```text
0
```

An explicit `service.adb.root=0` takes the shell privilege-drop branch. Otherwise it enters minijail without the UID/GID 2000 changes, retaining root.

## ADB authentication override

`amzn_is_adb_auth_disable_allowed` calls the same IDME reader and extracts bit 5:

```text
ubfx r0, r0, #5, #1
```

The string argument resolves to `usr_flags`, so the predicate is:

```c
bool amzn_is_adb_auth_disable_allowed(void) {
    return (fos_read_debug_flags("usr_flags") & 0x20) != 0;
}
```

In `adbd_main`, this is evaluated when `ro.adb.secure` is true. The allowed path clears the internal authentication-required flag.

## Important limitation

These conditions show the intended engineering/factory mechanism inside stock `adbd`. They do not prove that a retail secure-boot unit can alter the required kernel command line or protected IDME values. That trust boundary is the next bootloader/IDME research target.

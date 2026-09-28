# Amazon debug / root code paths in PS7715

This note documents code and configuration present in the shipping `almond-bt` PS7715/5585 firmware. Capability present in a binary is not the same thing as proving that a normal retail device can activate it.

## Shipping properties remain locked

`/system/etc/prop.default`:

```text
ro.secure=1
ro.adb.secure=1
ro.debuggable=0
persist.sys.usb.config=none
```

`/vendor/default.prop` also sets `ro.adb.secure=1` and `service.adb.tcp.port=5555`.

## Amazon-specific logic inside adbd

The shipped `/system/bin/adbd` is a 32-bit ARM static executable and is not stripped. Its symbol table exposes:

- `amzn_is_root_allowed`
- `amzn_is_adb_auth_disable_allowed`
- local `amzn_is_dev_unlocked`
- local `fos_read_debug_flags`
- source-unit name `amzn_fos_flags.cpp`

### Root permission predicate

Disassembly of `amzn_is_root_allowed()` proves this sequence:

1. Call `amzn_is_dev_unlocked()`.
2. If the device is not considered unlocked, return false.
3. Read `/proc/idme/fos_flags`.
4. Test bit `0x2`.
5. If set, log `amzn_fos: ADB: Auto-root succeeded` and return true.

### Device-unlocked predicate

`amzn_is_dev_unlocked()` reads `/proc/cmdline` and returns true when either string is present:

```text
androidboot.prod=0
androidboot.unlocked_kernel=true
```

The binary labels these states `eng_device` and `unlocked_kernel`.

### Effect on privilege dropping

In `adbd_main`, a false Amazon root predicate takes the normal minijail path and changes UID/GID to shell (2000).

When Amazon root permission is true, `adbd` reads:

```text
service.adb.root
```

The literal comparison value is `0`. If that property explicitly equals `0`, the normal shell privilege drop is taken. Otherwise the Amazon-allowed path enters the jail without the shell UID/GID change, retaining root privileges.

This is a deliberate developer/factory mechanism. It does not by itself prove a retail method for changing trusted boot state or protected IDME values.

## ADB authentication override predicate

`amzn_is_adb_auth_disable_allowed()` reads `/proc/idme/usr_flags` and extracts bit 5, i.e. `0x20`.

`adbd_main` first checks `ro.adb.secure`. If authentication is normally enabled, the Amazon predicate can clear the internal authentication-required flag when `usr_flags & 0x20` is set.

## IDME flags in vendor userspace

`/vendor/bin/devcfg.sh` defines:

```sh
fos_flags_path='/proc/idme/fos_flags'
dev_flags_path='/proc/idme/dev_flags'
FOS_DEV_FLAGS_USB_MODE_PHERIPHERAL=0x1
FOS_FLAGS_ADB_ROOT=2
```

It uses `dev_flags & 0x1` to initialize USB debugging mode. When `fos_flags & 0x2` is present it sets `persist.odm.disable_rescue=true`. The same script reads multiple IDME fields for model/panel configuration and explicitly recognizes `oem_data` containing `almond-bt`.

## Root-capable SELinux policy variants are shipped

System contains both normal and rootable variants:

- `/system/etc/selinux/plat_sepolicy.cil`
- `/system/etc/selinux/rootable_plat_sepolicy.cil`
- `/system/fireos/etc/selinux/fireos_sepolicy.cil`
- `/system/fireos/etc/selinux/rootable_fireos_sepolicy.cil`

Vendor contains:

- `/vendor/etc/selinux/vendor_sepolicy.cil`
- `/vendor/etc/selinux/rootable_vendor_sepolicy.cil`
- `/vendor/etc/selinux/plat_pub_versioned.cil`
- `/vendor/etc/selinux/rootable_plat_pub_versioned.cil`

The rootable policies include an SELinux `su` domain. Static `init` also contains hard-coded paths for the `rootable_*` policy files and the standard policies, proving runtime support is compiled in. The exact init policy-selection branch remains a separate reverse-engineering target.

## adbd root SELinux label

`/init.usb.rc` declares:

```text
service adbd /system/bin/adbd --root_seclabel=u:r:su:s0
    class core
    socket adbd stream 660 system system
    disabled
    seclabel u:r:adbd:s0
```

## Verified partitions still gate persistent modification

`/vendor/etc/fstab.amlogic` marks system and vendor with `verify`, the system image ships `/verity_key`, and the boot cmdline contains a verity key ID. The developer/root logic therefore does not by itself remove dm-verity or secure-boot protections.

## Proven conditions

The ADB-root predicate in this build is:

```text
(device cmdline contains androidboot.prod=0
 OR androidboot.unlocked_kernel=true)
AND
(/proc/idme/fos_flags & 0x2)
```

ADB-auth override is separately gated by:

```text
/proc/idme/usr_flags & 0x20
```

The next useful target is the bootloader/IDME trust path: determine where `prod`, `unlocked_kernel`, `fos_flags`, and `usr_flags` originate and what validates writes to them on retail secure-boot hardware.

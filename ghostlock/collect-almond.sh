#!/system/bin/sh
set -u
OUT=/sdcard/almond-ghostlock-probe.txt
exec >"$OUT" 2>&1

echo '=== identity ==='
date
uname -a
cat /proc/version 2>/dev/null || true
getprop ro.product.device
getprop ro.product.cpu.abi
getprop ro.product.cpu.abilist
getprop ro.build.version.release
getprop ro.build.version.sdk
getprop ro.build.version.incremental
getprop ro.build.display.id
getprop ro.boot.ammo.prod.var

echo '=== kernel/security ==='
cat /proc/sys/kernel/kptr_restrict 2>/dev/null || true
cat /proc/sys/kernel/dmesg_restrict 2>/dev/null || true
getenforce 2>/dev/null || true
ls -l /dev/ashmem 2>/dev/null || true
mount | grep -E 'configfs|debugfs|tracefs' || true
ls -ld /sys/kernel/config 2>/dev/null || true

echo '=== cpu ==='
cat /proc/cpuinfo

echo '=== config ==='
if [ -r /proc/config.gz ]; then
  echo '/proc/config.gz readable'
  zcat /proc/config.gz | grep -E 'CONFIG_(ARM64|ARM|ASHMEM|ANDROID_BINDER|CONFIGFS_FS|FUTEX|FUTEX_PI|SECURITY_SELINUX|RANDOMIZE_BASE|SLAB|SLUB|IO_URING)=' || true
else
  echo '/proc/config.gz unavailable'
fi

echo '=== symbols ==='
if [ -r /proc/kallsyms ]; then
  grep -E ' (init_task|init_cred|selinux_enforcing|security_hook_heads|kmalloc_caches|anon_pipe_buf_ops|ashmem_fops|ashmem_misc|random_fops|linux_banner)$' /proc/kallsyms 2>/dev/null || true
else
  echo '/proc/kallsyms unavailable'
fi

echo '=== memory/layout ==='
cat /proc/iomem 2>/dev/null | head -200 || true
cat /proc/meminfo 2>/dev/null || true

echo '=== done ==='
echo "$OUT"

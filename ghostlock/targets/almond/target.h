#ifndef TARGET_H
#define TARGET_H

/*
 * GhostLock almond-bt port scaffold.
 *
 * IMPORTANT: PS7715/5585 is not offset-compatible with karat/sunstone.
 * Do not substitute offsets from another target. This file intentionally
 * refuses to build until values are derived from almond's exact kernel.
 */
#ifndef ALMOND_OFFSETS_VERIFIED
#error "almond-bt offsets are not verified; derive them from PS7715 boot.img/kernel first"
#endif

/* Populate only after extracting the exact PS7715 kernel. */
#define KIMAGE_TEXT_BASE_DEFAULT 0ULL
#define P0_PAGE_OFFSET 0ULL
#define P0_PHYS_OFFSET 0ULL
#define P0_KERNEL_PHYS_LOAD 0ULL
#define KERNELSNITCH_IDENTITY_START 0ULL
#define KERNELSNITCH_IDENTITY_END 0ULL
#define DIRECT_MAP_BASE 0ULL
#define DIRECT_MAP_END 0ULL
#define VMEMMAP_START 0ULL

/* Required symbol/function offsets are intentionally omitted here. */

#endif

# PS7715 package inventory summary

Generated from the reconstructed filesystems.

| Location | Entries |
|---|---:|
| `system:/system/app` | 41 |
| `system:/system/priv-app` | 195 |
| `product:/app` | 3 |
| `product:/priv-app` | 1 |

## Notable OTA/update components

- `DeviceSoftwareOTA`
- `DeviceSoftwareOTAContracts`
- `DeviceSoftwareOTAIdleOverride`
- `FireOSDownloadProvider`
- `FireOSDownloadProviderUi`
- `com.amazon.tv.forcedotaupdater.v2`
- `RdmApplication`
- `RemoteSettingsAndroid`

## Notable TV/platform components

- `FireTVSystemUI`
- `com.amazon.tv.launcher`
- `AmlTvSettings`
- `DroidLogicTvInput`
- `DroidLogicTvProvider`
- `com.amazon.tv.channelscan`
- `com.amazon.tv.livetv`
- `com.amazon.tv.devicecontrol`
- `com.apple.airplay.amazon.airplay-stub`
- `HybridAdInfoService`

Run:

```bash
python tools/package_inventory.py out/
```

to generate the complete directory-name inventory from locally reconstructed images.

# Steam Grid Installation

## Where Steam reads custom artwork

Custom images live in `userdata/<steamid>/config/grid/`:

- Linux: `~/.local/share/Steam/userdata/<steamid>/config/grid/`
- Windows: `C:\Program Files (x86)\Steam\userdata\<steamid>\config\grid\`
- macOS: `~/Library/Application Support/Steam/userdata/<steamid>/config/grid/`

**Do not use `config/steamgrid/`.** Linux Steam does not read it; this is the most common reason a card stays default.

## File names and sizes

Prefix every file with the appid. Generate both appid variants (signed and unsigned), because Steam versions differ:

| Steam slot | Filename suffix | Recommended size |
| --- | --- | --- |
| Portrait grid | `_library_600x900.jpg` and `p.jpg` | 600x900 |
| Capsule | `_library_capsule.jpg` | 920x430 |
| Hero | `_library_hero.jpg` | 3840x1240 (1920x620 acceptable) |
| Header | `_header.jpg` | 460x215 |
| Logo | `_logo.png` | 1280x720 transparent |
| Icon | `_icon.png` | 512x512 |
| Legacy grid | `{appid}.png` / `{appid}_grid.png` | 460x215 |

The portrait (`library_600x900`/`p`) and hero files are what make the modern library card look right; include the others for older views.

## Signed vs unsigned appid

`shortcuts.vdf` stores the shortcut appid as a signed 32-bit integer (often negative). Convert:

- unsigned = signed + 4294967296 when signed is negative
- signed = unsigned - 4294967296 when unsigned is >= 2147483648

Example: `-1160374858` <-> `3134592438`.

Copy every artwork file to both prefixes. The sync script does this automatically.

## Verification

1. Close Steam completely, then relaunch it.
2. Open the library so the shortcut's tile loads.
3. Check `logs/steamui_librarycache.txt` (same directory as the Steam install) for the appid:
   - Good: no new `cache miss` line for that appid, and a final `Checked N, remaining 0` line.
   - Bad: `App <appid> reported a cache miss for asset type ...` still appears.
4. Optional: screenshot the library card for the user.

## Troubleshooting

- **Card still default after restart**: confirm files are in `config/grid/` (not `config/steamgrid/`), file names use the exact appid, and both signed/unsigned variants exist.
- **Cache miss still in log**: the names or directory are wrong; re-run the sync script and restart Steam again.
- **Blurry/incorrect crop**: use the highest-resolution cover available; pass `--hero-size 3840x1240` when the source is large enough.
- **shortcuts.vdf**: read it with the `vdf` module; never hand-edit it while Steam is running. Use the Steam UI to add/remove/rename shortcuts, then re-read the appid.

## Replacing an existing card

Regenerate the artwork, run `sync_steam_grid.py` with the same appid so it overwrites every variant, and restart Steam. Overwriting keeps stale legacy files from confusing the client.

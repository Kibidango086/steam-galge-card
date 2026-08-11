# Steam Grid Installation

## Where Steam reads custom artwork

Custom images live in `userdata/<steamid>/config/grid/`:

- Linux: `~/.local/share/Steam/userdata/<steamid>/config/grid/`
- Windows: `C:\Program Files (x86)\Steam\userdata\<steamid>\config\grid\`
- macOS: `~/Library/Application Support/Steam/userdata/<steamid>/config/grid/`

**Do not use `config/steamgrid/` for library artwork.** Linux Steam does not read it; this is the most common reason a card stays default. The one exception is the shortcut icon: `sync_steam_grid.py` copies the icon into `config/steamgrid/<unsigned-appid>_icon.png` and points the `shortcuts.vdf` `icon` field at that file.

## File names and sizes

Prefix every file with the appid. Generate both appid variants (signed and unsigned), because Steam versions differ:

| Steam slot | Filename suffix | Recommended size |
| --- | --- | --- |
| Portrait grid | `_library_600x900.jpg` and `p.jpg` | 600x900 |
| Capsule | `_library_capsule.jpg` | 920x430 |
| Hero (modern) | `_library_hero.jpg` | 3840x1240 (1920x620 acceptable) |
| Hero (legacy) | `_hero.jpg` | 1920x620 |
| Header | `_header.jpg` | 460x215 |
| Logo | `_logo.png` | 1280x720 transparent |
| Icon | `_icon.png` | 512x512 |
| Legacy grid | `{appid}.png` / `{appid}_grid.png` | 460x215 |

The portrait (`library_600x900`/`p`) and hero files are what make the modern library card look right; include the legacy `_hero.jpg` and the others for older views. `build_artwork.py` generates both hero names automatically.

## Shortcut icon

The library icon is read from the `icon` field in `shortcuts.vdf`, not from the grid folder. A plain `grid/<appid>_icon.png` can be ignored by some Steam clients, which is why the shortcut keeps showing the default exe icon.

- `sync_steam_grid.py --shortcuts-vdf ...` copies the icon to `config/steamgrid/<unsigned-appid>_icon.png` and updates the matching shortcut's `icon` field.
- Steam must be completely closed before that VDF update; the script writes a `.steam-galge-card.bak` backup first.
- The `icon` path must point at a file that exists after Steam restarts. Keep the `config/steamgrid/` copy in place.

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
- **Icon still default after restart**: check the `icon` field for that appid in `shortcuts.vdf`, confirm the referenced file exists under `config/steamgrid/`, and re-run `sync_steam_grid.py --shortcuts-vdf ...` before restarting Steam.
- **Wrong account / wrong userdata**: the game's shortcut is in only one `userdata/<steamid>/config/shortcuts.vdf`; install grid files into that same `<steamid>/config/grid/`.
- **Title still default or placeholder**: the library title comes from `AppName` in `shortcuts.vdf`; rename the shortcut in Steam UI (Steam must be running), then re-read the appid and restart Steam. The appid does not change when renaming.
- **Cache miss still in log**: the names or directory are wrong; re-run the sync script and restart Steam again.
- **Blurry/incorrect crop**: use the highest-resolution cover available; pass `--hero-size 3840x1240` when the source is large enough.
- **shortcuts.vdf**: read it with the `vdf` module; never hand-edit it while Steam is running. Use the Steam UI to add/remove/rename shortcuts, then re-read the appid.

## Replacing an existing card

Regenerate the artwork, run `sync_steam_grid.py` with the same appid so it overwrites every variant, and restart Steam. Overwriting keeps stale legacy files from confusing the client.

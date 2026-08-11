---
name: steam-galge-card
description: Create, fix, or replace the Steam library card of a non-Steam galgame added as a Steam shortcut. Use when the user asks to polish a non-Steam game's Steam card, add custom cover/hero/logo/icon artwork, make the library show a proper Japanese title instead of a default placeholder, or figure out why custom Steam grid art is not appearing. Gathers metadata from Kungal (鲲), VNDB, official game sites, and the game exe; generates Steam grid images; writes them to Steam's userdata grid folder; restarts Steam; and verifies with Steam logs.
---

# Steam Galge Card

## Overview

Give a non-Steam galgame a native-looking Steam library card: Japanese title, artwork in Steam grid sizes, and an icon from the game exe. The card is applied locally by writing images into Steam's `userdata/<steamid>/config/grid/` folder, then restarting Steam.

## User preferences (defaults)

- Use the Japanese title as the displayed game name.
- Use the game exe's icon for the Steam icon.
- Prefer official-site artwork; fall back to Kungal/VNDB covers and screenshots.
- When sources conflict, prefer: official site > Kungal > VNDB > SteamGridDB.

Ask the user only when a preference changes or sources genuinely conflict.

## Workflow

### 0. Create a work directory

Create `work/steam_card/<game-slug>/` in the current workspace (fall back to `/tmp/steam_card_<game-slug>/` when there is no workspace). Keep this layout:

```text
work/steam_card/<game-slug>/
  sources/   downloaded covers, heroes, logos, extracted icon PNGs
  out/       generated artwork from build_artwork.py
```

Save every downloaded image and extracted icon under `sources/`. Never write source files directly into Steam's `config/grid/`; only `sync_steam_grid.py` writes there.

### 1. Find the appid

The game must already be added as a non-Steam shortcut (add it in Steam UI; do not hand-edit `shortcuts.vdf` while Steam is running).

1. Locate `userdata`:
   - Linux: `~/.local/share/Steam/userdata/<steamid>/`
   - Windows: `C:\Program Files (x86)\Steam\userdata\<steamid>\`
   - macOS: `~/Library/Application Support/Steam/userdata/<steamid>/`
2. Read `config/shortcuts.vdf` with Python `vdf` (`vdf.binary_loads`) and match `AppName` to the game name.
3. Note the stored `appid` (signed int32, often negative) and always use both it and its unsigned counterpart (`signed + 2**32`) for grid files. Details: `references/steam-grid.md`.

### 2. Gather metadata and artwork

See `references/data-sources.md` for source-by-source instructions and exe icon extraction.

Collect at minimum:

- Japanese title, developer, release date
- Portrait cover (600x900 target; VNDB/Kungal covers work)
- Optional wide hero source (OGP image, key visual, or screenshot)
- Optional transparent logo PNG
- Icon PNG from the game exe

### 3. Generate artwork

```bash
python3 scripts/build_artwork.py \
  --cover work/steam_card/<game-slug>/sources/cover.png \
  --hero work/steam_card/<game-slug>/sources/hero.png \
  --logo work/steam_card/<game-slug>/sources/logo.png \
  --icon work/steam_card/<game-slug>/sources/icon.png \
  --prefix lllj \
  --out-dir work/steam_card/<game-slug>/out
```

Outputs standard Steam sizes: 600x900 portrait, 920x430 capsule, 460x215 header, 1920x620 hero (official 3840x1240 is available via `--hero-size`), 1280x720 logo, and 512x512 icon. Omit `--hero`/`--logo`/`--icon` when the source is unavailable; the script skips those files.

### 4. Install grid files

```bash
python3 scripts/sync_steam_grid.py \
  --source-dir work/steam_card/<game-slug>/out \
  --prefix lllj \
  --grid-dir ~/.local/share/Steam/userdata/<steamid>/config/grid \
  --appid -1160374858
```

The script copies every generated file to both the signed and unsigned appid filenames. It can also read the appid from `shortcuts.vdf` by game name: see `--help`.

### 5. Restart Steam and verify

1. Close Steam completely, then relaunch it.
2. Open the library so the shortcut's grid cache is refreshed.
3. Check `logs/steamui_librarycache.txt` (next to the Steam install) for the appid. A successful install shows no new `cache miss` line for that appid and ends with `Checked N, remaining 0`. Take a library screenshot when the user wants visual proof.
4. If the card is still default, see troubleshooting in `references/steam-grid.md`.

## Replacing or updating a card

Run steps 3-5 again with the same appid. The sync script overwrites the existing files with the same names, so no stale files remain. Changing only the icon or title still requires the full grid sync so all appid variants stay in sync.

## Requirements

- Python 3 with Pillow and `vdf`
- `icoutils` (`wrestool`, `icotool`) only when extracting the icon from a Windows exe
- A running local Steam installation on the same machine

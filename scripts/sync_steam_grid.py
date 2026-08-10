#!/usr/bin/env python3
"""Copy generated Steam artwork into the userdata grid folder.

Writes every generated file under both the signed and unsigned appid names so
different Steam client versions find the card.

Examples:
    python3 sync_steam_grid.py --source-dir out --prefix lllj \
        --grid-dir ~/.local/share/Steam/userdata/123/config/grid --appid -1160374858

    python3 sync_steam_grid.py --source-dir out --prefix lllj \
        --shortcuts-vdf ~/.local/share/Steam/userdata/123/config/shortcuts.vdf \
        --name "ライムライト・レモネードジャム"
"""

import argparse
import shutil
import sys
from pathlib import Path


def appid_variants(appid):
    if appid < 0:
        return appid, appid + (1 << 32)
    if appid >= (1 << 31):
        return appid - (1 << 32), appid
    return appid, appid


def find_appid(shortcuts_path, name):
    try:
        import vdf
    except ImportError:
        sys.exit("Python module 'vdf' is required: pip install vdf")

    with open(shortcuts_path, "rb") as fh:
        shortcuts = vdf.binary_loads(fh.read()).get("shortcuts", {})

    needle = name.casefold()
    matches = [
        entry
        for entry in shortcuts.values()
        if needle in str(entry.get("AppName", "")).casefold()
    ]
    if not matches:
        names = "\n".join(
            f"- {entry.get('AppName', '<unnamed>')} (appid {entry.get('appid')})"
            for entry in shortcuts.values()
        )
        sys.exit(f"No shortcut matches {name!r}. Available:\n{names}")
    if len(matches) > 1:
        sys.exit(f"{name!r} matches multiple shortcuts; pass --appid explicitly.")
    return int(matches[0]["appid"])


def artwork_files(source_dir, prefix):
    for path in sorted(source_dir.iterdir()):
        name = path.name
        if (
            name.startswith(f"{prefix}_")
            or name.startswith(f"{prefix}.")
            or name.startswith(f"{prefix}p.")
        ):
            yield path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, help="Directory from build_artwork.py")
    parser.add_argument("--prefix", required=True, help="Prefix used by build_artwork.py")
    parser.add_argument("--grid-dir", required=True, help="userdata/<steamid>/config/grid")
    parser.add_argument("--appid", type=int, help="Signed or unsigned shortcut appid")
    parser.add_argument("--shortcuts-vdf", help="shortcuts.vdf to read the appid from")
    parser.add_argument("--name", help="Shortcut name to match in shortcuts.vdf")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without copying")
    args = parser.parse_args()

    if args.appid is None:
        if not args.shortcuts_vdf or not args.name:
            sys.exit("Provide --appid or both --shortcuts-vdf and --name.")
        args.appid = find_appid(args.shortcuts_vdf, args.name)

    signed, unsigned = appid_variants(args.appid)
    grid_dir = Path(args.grid_dir).expanduser()
    grid_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src in artwork_files(Path(args.source_dir), args.prefix):
        suffix = src.name[len(args.prefix) :]
        for appid in sorted({signed, unsigned}):
            dest = grid_dir / f"{appid}{suffix}"
            print(f"{'[dry-run]' if args.dry_run else ''} {src.name} -> {dest.name}")
            copied += 1
            if not args.dry_run:
                shutil.copy2(src, dest)

    print(
        f"{'Would sync' if args.dry_run else 'Synced'} {copied} files to {grid_dir} "
        f"(appids {signed} and {unsigned})"
    )


if __name__ == "__main__":
    main()

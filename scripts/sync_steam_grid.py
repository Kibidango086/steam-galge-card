#!/usr/bin/env python3
"""Copy generated Steam artwork into the userdata grid folder.

Writes every generated file under both the signed and unsigned appid names so
different Steam client versions find the card. When an icon is available and
--shortcuts-vdf is given, also copies the icon to config/steamgrid/ and points
the shortcut's icon field at it.

Steam must be fully closed before editing shortcuts.vdf. Close it with
`steam -shutdown`, wait for the process to exit, run this script, then start
Steam again.

Examples:
    python3 sync_steam_grid.py --source-dir work/steam_card/game/out \
        --prefix game --grid-dir ~/.local/share/Steam/userdata/123/config/grid \
        --shortcuts-vdf ~/.local/share/Steam/userdata/123/config/shortcuts.vdf \
        --name "ゲーム名"

    python3 sync_steam_grid.py --source-dir out --prefix lllj \
        --grid-dir ~/.local/share/Steam/userdata/123/config/grid --appid -1160374858
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


def appid_variants(appid):
    if appid < 0:
        return appid, appid + (1 << 32)
    if appid >= (1 << 31):
        return appid - (1 << 32), appid
    return appid, appid


def load_shortcuts(shortcuts_path):
    try:
        import vdf
    except ImportError:
        sys.exit("Python module 'vdf' is required: pip install vdf")
    with open(shortcuts_path, "rb") as fh:
        return vdf.binary_loads(fh.read())


def find_appid(shortcuts_path, name):
    data = load_shortcuts(shortcuts_path)
    shortcuts = data.get("shortcuts", {})
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


def update_icon_field(shortcuts_path, appid, icon_path, dry_run):
    import vdf

    vdf_path = Path(shortcuts_path).expanduser()
    data = load_shortcuts(vdf_path)
    shortcuts = data.get("shortcuts", {})
    signed, _ = appid_variants(appid)
    target = None
    for entry in shortcuts.values():
        try:
            if int(entry.get("appid", 0)) == signed:
                target = entry
                break
        except (TypeError, ValueError):
            continue
    if target is None:
        sys.exit(f"shortcuts.vdf has no entry with appid {signed}; cannot update icon.")

    print(f"{'[dry-run] ' if dry_run else ''}icon -> {target.get('AppName', '?')}: {icon_path}")
    if dry_run:
        return

    backup = vdf_path.with_name(vdf_path.name + ".steam-galge-card.bak")
    shutil.copy2(vdf_path, backup)
    target["icon"] = str(icon_path)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(vdf_path.parent), prefix=vdf_path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            vdf.binary_dump(data, fh)
        os.replace(tmp_name, vdf_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    print(f"Updated {vdf_path} (backup: {backup})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, help="Directory from build_artwork.py")
    parser.add_argument("--prefix", required=True, help="Prefix used by build_artwork.py")
    parser.add_argument("--grid-dir", required=True, help="userdata/<steamid>/config/grid")
    parser.add_argument("--appid", type=int, help="Signed or unsigned shortcut appid")
    parser.add_argument("--shortcuts-vdf", help="shortcuts.vdf to read appid/update icon field")
    parser.add_argument("--name", help="Shortcut name to match in shortcuts.vdf")
    parser.add_argument("--icon-source", help="Icon file; defaults to <source-dir>/<prefix>_icon.png")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without copying")
    args = parser.parse_args()

    if args.appid is None:
        if not args.shortcuts_vdf or not args.name:
            sys.exit("Provide --appid or both --shortcuts-vdf and --name.")
        args.appid = find_appid(args.shortcuts_vdf, args.name)

    signed, unsigned = appid_variants(args.appid)
    grid_dir = Path(args.grid_dir).expanduser()
    grid_dir.mkdir(parents=True, exist_ok=True)
    source_dir = Path(args.source_dir)

    copied = 0
    for src in artwork_files(source_dir, args.prefix):
        suffix = src.name[len(args.prefix) :]
        for appid in sorted({signed, unsigned}):
            dest = grid_dir / f"{appid}{suffix}"
            print(f"{'[dry-run] ' if args.dry_run else ''}{src.name} -> {dest.name}")
            copied += 1
            if not args.dry_run:
                shutil.copy2(src, dest)

    icon_src = Path(args.icon_source).expanduser() if args.icon_source else source_dir / f"{args.prefix}_icon.png"
    if icon_src.is_file():
        steamgrid_dir = grid_dir.parent / "steamgrid"
        for appid in sorted({signed, unsigned}):
            dest = steamgrid_dir / f"{appid}_icon.png"
            print(f"{'[dry-run] ' if args.dry_run else ''}icon {icon_src.name} -> {dest}")
            if not args.dry_run:
                steamgrid_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(icon_src, dest)

        if args.shortcuts_vdf:
            icon_path = steamgrid_dir / f"{unsigned}_icon.png"
            print("Make sure Steam is fully closed before this step.")
            update_icon_field(args.shortcuts_vdf, signed, icon_path, args.dry_run)
        else:
            print(
                "Icon copied to config/steamgrid/. Pass --shortcuts-vdf to also "
                "point the shortcut's icon field at it."
            )
    elif args.shortcuts_vdf:
        print("No icon file found; skipping shortcuts.vdf icon update.")

    print(
        f"{'Would sync' if args.dry_run else 'Synced'} {copied} files to {grid_dir} "
        f"(appids {signed} and {unsigned})"
    )


if __name__ == "__main__":
    main()

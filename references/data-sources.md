# Data Sources

## Kungal (鲲 Galgame)

- Page pattern: `https://www.kungal.com/galgame/<id>` (example: `3839` for ライムライト・レモネードジャム).
- Provides: Chinese title/description, developer, release date, cover, screenshots, and download links.
- How to use: fetch the page (`curl -L`), then extract `og:image`/`twitter:image` for the cover and the page's structured info. If the game ID is unknown, search the site or a search engine with the Japanese title plus `kungal`.
- Preferred use: fallback cover/screenshots when the official site is not available.

## VNDB

- Page pattern: `https://vndb.org/v<id>` (example: `v56650`).
- Provides: English metadata, Japanese aliases, developer, release date, languages, and tags.
- API (read-only): `https://api.vndb.org/kana/vn` with JSON filters; e.g. find by title with `["search","=","<title>"]` and request fields like `title`, `aliases`, `developers`, `released`.
- Preferred use: authoritative release date/developer and a good portrait cover; the cover is usually croppable to 600x900.

## Official game site

- Find via the developer/publisher site (e.g. Yuzusoft product pages) or by searching the Japanese title.
- Provides: the official Japanese title, key visual, transparent logo, release date, and high-resolution artwork.
- Extract images from `og:image`/`twitter:image` meta tags or the page's image tags; download at full size.
- Preferred use: primary title and artwork, especially the logo.

## Steam

- For a game that also has a real Steam page, the store page provides canonical English/Japanese title and official grid artwork.
- For a non-Steam shortcut, Steam itself is only the local target: the appid in `shortcuts.vdf`, the `userdata/<steamid>/config/grid/` folder, and `logs/steamui_librarycache.txt`.
- Optional fallback: SteamGridDB provides ready-made 600x900/capsule/hero/logo artwork if the user does not want generated crops.

## Game exe

- The game's `.exe` usually contains the product icon. Extract with `icoutils`:

```bash
wrestool -x -t14 "game.exe" -o icon.ico
icotool -x icon.ico -o icon_extracted/
```

- Pick the largest square PNG from `icon_extracted/` as the icon source.
- If `wrestool`/`icotool` are not installed, check the game folder for an existing `.ico`/`.png` icon, or ask the user for one. Do not install packages without user consent.

## Downloading images

- Use `curl -L -A "Mozilla/5.0" -o out.png <url>` for site images.
- Verify every downloaded image with Pillow (`Image.open`) before generating artwork; delete unusable files (too small, corrupted, non-image HTML).

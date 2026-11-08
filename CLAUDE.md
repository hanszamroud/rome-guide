# Notes for Claude working on this repository

Rome Walk is an offline-first walking guide (static site, installed on iPhone via Safari "Add to Home Screen", hosted on GitHub Pages). The trip is Saturday 14 November 2026. Two English-speaking adults, both on iPhone; one is an engineer. Interests: history, politics, philosophy, engineering, daily life. Keep gore and post-Roman history light.

## Rules

- Offline is the point. No CDNs, web fonts, analytics or network calls. Every file the app needs must be listed by `tools/build_data.py` in `data/precache.js`.
- Never edit `data/stops.js`, `data/precache.js`, `maps/*` or `IMAGES.md` by hand. Edit `CONTENT.md` or `tools/stops_meta.json`, then run `python3 tools/build_data.py` and fix anything it reports.
- Keep the format of `CONTENT.md`: `### N. Title (CORE)`, then `Threads: ...`, `**Core.**` or `**Script.**`, optional `**Deep dive: title.**`, `**Look for.**`, `**Images.**`. The parser depends on it.
- Writing style for scripts: written to be heard. Short sentences, concrete numbers, one hook per stop. Core scripts 60–90 seconds; deep dives 2–3 minutes. Flag debated claims as debated.
- Images: public domain or open licence only, with the credit line in `stops_meta.json`. About 1200 px wide, under 300 KB. No photos of identifiable private people.
- Plain JavaScript, no frameworks, no build step. Test on a narrow (390 px) viewport and in dark mode.

## Open tasks

1. Add photos and historic drawings listed as unchecked in `IMAGES.md` (Wikimedia Commons is a good source; Piranesi's Vedute di Roma are public domain).
2. Check stop coordinates in `tools/stops_meta.json` against OpenStreetMap; they are approximate.
3. Optionally generate recorded audio with `tools/make_audio.py` (macOS only).
4. After changes: run the build, serve with `python3 -m http.server`, confirm the Plan tab reports all files stored, and push.

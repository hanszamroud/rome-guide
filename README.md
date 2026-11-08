# Rome Walk

An offline audio walking guide for the Palatine Hill, the Roman Forum and the Colosseum, built for Saturday 14 November 2026.

- 25 stops, 14 of them core (about 1.5 hours with walking; about 4 hours with every deep dive and optional stop).
- Every stop has a narrated script, an optional deep dive, things to look for, and diagrams.
- A map with your live GPS position, which works in flight mode.
- Audio is read by the iPhone's own voice, or by recorded files if you make them (see below).
- Once installed, it needs no internet at all. Nothing is tracked; your location never leaves the phone.

It is a plain website (HTML, CSS, JavaScript) with no build step, hosted free on GitHub Pages and installed on the iPhone Home Screen.

## 1. Put it on GitHub Pages (about 5 minutes)

1. On github.com, create a new repository, for example `rome-walk`. Make it **Public**: free GitHub Pages needs a public repository.
2. In the new repository, click **Add file › Upload files**. Drag in **everything inside this folder**, keeping the folders (`data`, `img`, `icons`, `maps`, `tools`, `audio`). Commit.
3. Go to **Settings › Pages**. Under **Build and deployment**, set Source to **Deploy from a branch**, branch **main**, folder **/ (root)**. Save.
4. After a minute or two the site is live at `https://<your-username>.github.io/rome-walk/`.

With the GitHub command line instead:

```
cd rome-walk
git init && git add . && git commit -m "Rome Walk"
gh repo create rome-walk --public --source . --push
gh api -X POST repos/{owner}/rome-walk/pages -f "source[branch]=main" -f "source[path]=/"
```

## 2. Install on both iPhones

1. Open the Pages address in **Safari** (not Chrome).
2. Tap **Share › Add to Home Screen**.
3. Open **Rome Walk from the Home Screen icon** while still online. The Home Screen app keeps its own offline storage, separate from Safari, so this step matters.
4. Go to the **Plan** tab. Wait until it says **Ready: all files stored on this phone**.

## 3. Before you fly: checklist

- [ ] **Offline test.** Switch on flight mode, open the app from the Home Screen, play a stop, open the Map, tap Start GPS.
- [x] **Recorded voice.** Every stop is recorded with the ElevenLabs voice Chris Brift (`tools/make_audio_elevenlabs.py`). The iPhone voice is only a backup: for a better backup, Settings › Accessibility › Read & Speak › Voices › English (Spoken Content on iOS 18 and older), download an **Enhanced** or **Premium** voice and pick it in the app's Plan tab.
- [ ] **Offline Apple Maps.** In Apple Maps, tap your profile › Offline Maps and download central Rome. The "Show in Maps" buttons then work without data.
- [ ] **Optional backup map.** Download the free Organic Maps app with Rome offline, then open `maps/rome-guide.kml` (from the Plan tab) to get every stop as a pin.
- [ ] **Screen lock.** iPhone stops spoken text when the screen locks. On the day, set Settings › Display & Brightness › Auto-Lock to a long time, or make recorded audio (section 4), which keeps playing.
- [ ] **Shared listening.** Both pairs of AirPods can listen to one iPhone: connect your AirPods, then in Control Center tap the AirPlay icon › **Share Audio** and bring the second pair close. One phone can then play for both of you.
- [ ] **Power.** GPS plus screen for 5 hours drains batteries: bring a power bank.
- [ ] **Pin positions.** Stop coordinates are approximate (about 20–40 m). If any look off on the map, fix them in `tools/stops_meta.json` and rebuild.

## 4. Optional: recorded audio (needs a Mac)

Recorded files sound better and keep playing with the screen locked.

```
python3 tools/make_audio.py --list-voices
python3 tools/make_audio.py --voice "Daniel"       # or a Premium voice you downloaded
```

This writes `audio/NN-core.m4a` and `audio/NN-deep.m4a` for every stop and rebuilds the data. Upload the new `audio` files and `data` folder to GitHub, then open the app once online so it stores them. The app uses a recording where one exists and falls back to the phone's voice everywhere else.

## Editing the guide

All prose lives in `CONTENT.md`. Coordinates, minutes per stop and image lists live in `tools/stops_meta.json`. After changing either:

```
python3 tools/build_data.py
```

This regenerates `data/stops.js`, the offline file list `data/precache.js`, the map pins in `maps/`, and `IMAGES.md`. It also reports problems such as a missing image. Upload the changed files; the app picks up the new version the next time it opens online.

## Adding photos

Planned photos and historic drawings for every stop are listed in `IMAGES.md`. To add one:

1. Find a public-domain or openly licensed image, for example on Wikimedia Commons. Piranesi's 18th-century engravings of Rome are public domain and ideal for "then and now".
2. Resize it to about 1200 px wide and under 300 KB, and save it in `img/photos/`.
3. Add it to that stop in `tools/stops_meta.json`, with a caption and the credit line the licence requires:
   `"photos": [{"file": "titus-piranesi.jpg", "caption": "The arch in the 1750s, still built into medieval walls", "credit": "G. B. Piranesi, public domain, via Wikimedia Commons"}]`
4. Run `python3 tools/build_data.py`.

## Files

| Path | What it is |
| --- | --- |
| `index.html`, `styles.css`, `app.js` | The app |
| `sw.js` | Service worker: stores everything for offline use |
| `manifest.webmanifest`, `icons/` | Home Screen app details |
| `CONTENT.md` | All guide text: edit this |
| `data/stops.js`, `data/precache.js` | Generated by `tools/build_data.py`, do not edit |
| `img/diagrams/` | SVG diagrams drawn for this guide |
| `img/photos/` | Photos and historic drawings (add your own) |
| `audio/` | Optional recorded audio |
| `maps/` | Stop pins as KML and GPX |
| `tools/` | Build, diagram and audio scripts; `stops_meta.json` |

## Run it locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000. Offline storage only works over `https` or `localhost`.

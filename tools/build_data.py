#!/usr/bin/env python3
"""Build the app's data files from CONTENT.md and tools/stops_meta.json.

Run from the repository root:  python3 tools/build_data.py

Writes:
  data/stops.js        all stop content, coordinates, images, audio paths
  data/precache.js     list of files the service worker stores for offline use
  maps/rome-guide.kml  pins for Organic Maps / Google My Maps
  maps/rome-guide.gpx  same pins as GPX
  IMAGES.md            image checklist per stop
"""
import hashlib
import json
import os
import re
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def strip_md(text):
    """Remove markdown emphasis so text reads cleanly and speaks cleanly."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()


def parse_content(md):
    sections, stops = [], []
    section = None
    stop = None
    field = None  # current field being filled

    def finish_stop():
        if stop:
            for k in ("core", "deep"):
                stop[k] = "\n\n".join(p for p in stop[k] if p)
            stops.append(stop)

    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block:
            continue
        m2 = re.match(r"^## (.+)$", block)
        m3 = re.match(r"^### (\d+)\. (.+)$", block)
        if m2:
            finish_stop()
            stop = None
            title = m2.group(1).strip()
            section = {"title": title, "intro": "", "stops": []}
            sections.append(section)
            continue
        if m3:
            finish_stop()
            num = int(m3.group(1))
            raw_title = m3.group(2).strip()
            core = "(CORE)" in raw_title
            title = raw_title.replace("(CORE)", "").strip()
            stop = {
                "n": num, "title": title, "core": [], "deep": [],
                "isCore": core, "deepTitle": "", "threads": [],
                "note": "", "lookFor": "", "imagesPlanned": "",
                "section": len(sections) - 1,
            }
            section["stops"].append(num)
            field = None
            continue
        if stop is None:
            if section is not None and not section["intro"]:
                section["intro"] = strip_md(block)
            continue
        if block.startswith("Threads:"):
            rest = block[len("Threads:"):].strip().rstrip(".")
            parts = [p.strip() for p in rest.split(".")]
            stop["threads"] = [t.strip() for t in parts[0].split(",") if t.strip()]
            stop["note"] = ". ".join(p for p in parts[1:] if p).strip()
            continue
        m = re.match(r"^\*\*(Core|Script)\.\*\*\s*(.*)$", block, re.S)
        if m:
            field = "core"
            stop["core"].append(strip_md(m.group(2)))
            continue
        m = re.match(r"^\*\*Deep dive: (.+?)\.\*\*\s*(.*)$", block, re.S)
        if m:
            field = "deep"
            stop["deepTitle"] = m.group(1).strip()
            stop["deep"].append(strip_md(m.group(2)))
            continue
        m = re.match(r"^\*\*Look for\.\*\*\s*(.*)$", block, re.S)
        if m:
            field = None
            stop["lookFor"] = strip_md(m.group(1))
            continue
        m = re.match(r"^\*\*Images\.\*\*\s*(.*)$", block, re.S)
        if m:
            field = None
            stop["imagesPlanned"] = strip_md(m.group(1))
            continue
        if field in ("core", "deep"):
            stop[field].append(strip_md(block))
    finish_stop()
    return sections, stops


def svg_title(path):
    try:
        m = re.search(r"<title>(.*?)</title>", read(path), re.S)
        return m.group(1).strip() if m else ""
    except FileNotFoundError:
        return None


def main():
    sections, stops = parse_content(read("CONTENT.md"))
    meta = json.loads(read("tools/stops_meta.json"))
    problems = []

    for s in stops:
        m = meta["stops"].get(str(s["n"]))
        if not m:
            problems.append(f"stop {s['n']}: missing in stops_meta.json")
            continue
        s["lat"], s["lon"], s["minutes"] = m["lat"], m["lon"], m["minutes"]
        images = []
        for d in m.get("diagrams", []):
            cap = svg_title(f"img/diagrams/{d}")
            if cap is None:
                problems.append(f"stop {s['n']}: diagram {d} not found")
                continue
            images.append({"src": f"img/diagrams/{d}", "caption": cap, "kind": "diagram"})
        for p in m.get("photos", []):
            if not os.path.exists(os.path.join(ROOT, "img/photos", p["file"])):
                problems.append(f"stop {s['n']}: photo {p['file']} not found")
                continue
            images.append({"src": f"img/photos/{p['file']}", "caption": p.get("caption", ""),
                           "credit": p.get("credit", ""), "kind": "photo"})
        s["images"] = images
        audio = {}
        for part in ("core", "deep"):
            for ext in ("m4a", "mp3"):
                rel = f"audio/{s['n']:02d}-{part}.{ext}"
                if os.path.exists(os.path.join(ROOT, rel)):
                    audio[part] = rel
                    break
        s["audio"] = audio
        if not s["core"]:
            problems.append(f"stop {s['n']}: no core/script text")

    nums = [s["n"] for s in stops]
    if nums != list(range(1, len(nums) + 1)):
        problems.append(f"stop numbers not sequential: {nums}")

    data = {"sections": sections, "stops": stops, "places": meta["places"]}
    write("data/stops.js", "// Generated by tools/build_data.py from CONTENT.md. Do not edit by hand.\n"
          "window.GUIDE = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

    # Offline file list for the service worker
    files = ["./", "index.html", "styles.css", "app.js", "manifest.webmanifest", "data/stops.js",
             "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"]
    for folder in ("img/diagrams", "img/photos", "audio"):
        full = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(full)):
            if name.startswith(".") or name.endswith(".md") or name.endswith(".txt"):
                continue
            files.append(f"{folder}/{name}")
    h = hashlib.sha1()
    for f in files:
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                h.update(fh.read())
    version = h.hexdigest()[:10]
    write("data/precache.js", "// Generated by tools/build_data.py.\n"
          f"self.PRECACHE_VERSION = {json.dumps(version)};\n"
          f"self.PRECACHE_FILES = {json.dumps(files, indent=1)};\n")

    # Map pins
    def pins():
        for s in stops:
            label = f"{s['n']}. {s['title']}" + (" (core)" if s["isCore"] else "")
            yield label, s["lat"], s["lon"], s["lookFor"]
        for p in meta["places"]:
            yield p["name"], p["lat"], p["lon"], ""

    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Rome guide 14 Nov</name>']
    for name, lat, lon, desc in pins():
        kml.append(f"<Placemark><name>{escape(name)}</name><description>{escape(desc)}</description>"
                   f"<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>")
    route = " ".join(f"{s['lon']},{s['lat']},0" for s in stops if s["n"] <= 18)
    kml.append(f"<Placemark><name>Morning route</name><LineString><coordinates>{route}</coordinates></LineString></Placemark>")
    kml.append("</Document></kml>")
    write("maps/rome-guide.kml", "\n".join(kml) + "\n")

    gpx = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<gpx version="1.1" creator="rome-guide" xmlns="http://www.topografix.com/GPX/1/1">']
    for name, lat, lon, desc in pins():
        gpx.append(f'<wpt lat="{lat}" lon="{lon}"><name>{escape(name)}</name><desc>{escape(desc)}</desc></wpt>')
    gpx.append("</gpx>")
    write("maps/rome-guide.gpx", "\n".join(gpx) + "\n")

    # Image checklist
    lines = ["# Image checklist", "",
             "Generated by `tools/build_data.py`. Diagrams marked done are already in `img/diagrams`. "
             "Photos and historic drawings still need adding: see README, section \"Adding photos\".", ""]
    for s in stops:
        m = meta["stops"][str(s["n"])]
        lines.append(f"## {s['n']}. {s['title']}")
        lines.append("")
        lines.append(f"- Planned: {s['imagesPlanned']}")
        for d in m.get("diagrams", []):
            lines.append(f"- [x] Diagram: `img/diagrams/{d}`")
        for p in m.get("photos", []):
            lines.append(f"- [x] Photo: `img/photos/{p['file']}` ({p.get('credit', 'credit missing')})")
        if not m.get("photos"):
            lines.append("- [ ] Photos / historic drawings: none added yet")
        lines.append("")
    write("IMAGES.md", "\n".join(lines))

    core = [s for s in stops if s["isCore"]]
    print(f"{len(stops)} stops ({len(core)} core) in {len(sections)} sections; "
          f"{sum(len(s['images']) for s in stops)} images; "
          f"{sum(len(s['audio']) for s in stops)} audio files; precache {len(files)} files, version {version}")
    words = sum(len((s['core'] + ' ' + s['deep']).split()) for s in stops)
    core_words = sum(len(s['core'].split()) for s in core)
    print(f"Narration: {words} words total (~{words/150:.0f} min); core stops only ~{core_words/150:.0f} min")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Optional: record every script as an audio file using a Mac's built-in voices.

Recorded files sound better than live speech and keep playing when the iPhone screen
locks. Without them, the app reads the text aloud with the iPhone's own voice.

Requires macOS (uses the built-in `say` and `afconvert` commands). Run from the repo root:

    python3 tools/make_audio.py                 # default voice: Daniel (British English)
    python3 tools/make_audio.py --voice "Serena (Premium)" --rate 175
    python3 tools/make_audio.py --list-voices   # show English voices on this Mac

For the best quality, first download a Premium or Enhanced voice on the Mac:
System Settings > Accessibility > Spoken Content > System Voice > Manage Voices.

Writes audio/NN-core.m4a and audio/NN-deep.m4a, then rebuilds data/stops.js.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_data import parse_content, read  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Daniel")
    ap.add_argument("--rate", type=int, default=170, help="words per minute (default 170)")
    ap.add_argument("--only", type=int, nargs="*", help="stop numbers to (re)record")
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()

    if not shutil.which("say") or not shutil.which("afconvert"):
        sys.exit("This script needs macOS (the 'say' and 'afconvert' commands).")
    if args.list_voices:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        print("\n".join(l for l in out.splitlines() if " en_" in l or " en-" in l))
        return

    _, stops = parse_content(read("CONTENT.md"))
    os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for s in stops:
            if args.only and s["n"] not in args.only:
                continue
            for part in ("core", "deep"):
                text = s[part]
                if not text:
                    continue
                intro = f"Stop {s['n']}. {s['title']}." if part == "core" else f"Deep dive: {s['deepTitle']}."
                txt = os.path.join(tmp, "t.txt")
                with open(txt, "w", encoding="utf-8") as f:
                    # a blank line between paragraphs gives a natural pause
                    f.write(intro + "\n\n" + text.replace("\n\n", "\n\n[[slnc 400]]\n\n"))
                aiff = os.path.join(tmp, "t.aiff")
                out = os.path.join(ROOT, "audio", f"{s['n']:02d}-{part}.m4a")
                subprocess.run(["say", "-v", args.voice, "-r", str(args.rate), "-f", txt, "-o", aiff], check=True)
                subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", aiff, out], check=True)
                print("wrote", os.path.relpath(out, ROOT))
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_data.py")], check=True)


if __name__ == "__main__":
    main()

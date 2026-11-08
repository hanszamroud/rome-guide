#!/usr/bin/env python3
"""Optional: record every script as an MP3 with an ElevenLabs voice.

Needs an ElevenLabs API key with Text to Speech permission, in the environment:

    export ELEVENLABS_API_KEY=sk_...
    python3 tools/make_audio_elevenlabs.py                  # all stops, skips files that exist
    python3 tools/make_audio_elevenlabs.py --only 3 14      # (re)record these stops
    python3 tools/make_audio_elevenlabs.py --force          # re-record everything

Writes audio/NN-core.mp3 and audio/NN-deep.mp3 (64 kbps mono), then rebuilds data/stops.js.
The default voice is Chris Brift. The full guide is about 33,000 characters, so about
33,000 credits with the default model.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_data import parse_content, read  # noqa: E402

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_64"


def tts(key, voice, model, text, prev_text=None, next_text=None):
    body = {"text": text, "model_id": model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0,
                               "use_speaker_boost": True}}
    if prev_text:
        body["previous_text"] = prev_text
    if next_text:
        body["next_text"] = next_text
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(body).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json",
                                          "Accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            sys.exit(f"ElevenLabs error {e.code}: {msg}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(5)
                continue
            sys.exit(f"Network error: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="UEKYgullGqaF0keqT8Bu", help="voice ID (default: Chris Brift)")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--only", type=int, nargs="*", help="stop numbers to (re)record")
    ap.add_argument("--force", action="store_true", help="re-record files that already exist")
    args = ap.parse_args()

    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY first.")

    _, stops = parse_content(read("CONTENT.md"))
    os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
    total = 0
    for s in stops:
        if args.only and s["n"] not in args.only:
            continue
        for part in ("core", "deep"):
            text = s[part]
            if not text:
                continue
            out = os.path.join(ROOT, "audio", f"{s['n']:02d}-{part}.mp3")
            if os.path.exists(out) and not args.force and not args.only:
                continue
            intro = f"Stop {s['n']}. {s['title']}." if part == "core" else f"Deep dive: {s['deepTitle']}."
            # a paragraph break plus a short pause between paragraphs
            script = intro + "\n\n" + text.strip().replace("\n\n", ' <break time="0.6s" />\n\n')
            audio = tts(key, args.voice, args.model, script)
            with open(out, "wb") as f:
                f.write(audio)
            total += len(script)
            print(f"wrote {os.path.relpath(out, ROOT)} ({len(audio) // 1024} KB, {len(script)} chars)")
    print(f"characters sent: {total}")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_data.py")], check=True)


if __name__ == "__main__":
    main()

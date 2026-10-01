"""Generate the voiceover, one mp3 per shot, with Doubao seed-audio-1.0.

Reads docs/02-旁白稿.txt and writes public/audio/vo/<shot>.mp3 plus
public/audio/vo/durations.json (seconds per shot, measured with ffprobe).

Credentials come from the environment, never from this repo:
  VOLC_TTS_API_KEY        sent as X-Api-Key (preferred, matches the console sample)
  VOLC_TTS_APP_ID         fallback pair, sent as X-Api-App-Id / X-Api-Access-Key
  VOLC_TTS_ACCESS_TOKEN
Optional:
  VOLC_TTS_URL            default https://openspeech.bytedance.com/api/v3/tts/create
  VOICE_SPEAKER           Doubao TTS 2.0 voice id that pins the timbre across shots
                          (default zh_male_m191_uranus_bigtts; set to "" to rely on the prompt only)
  SPEECH_RATE             audio_config.speech_rate, default 0

Usage:
  python3 scripts/tts_seed_audio.py --dry-run            # print the request for S00
  python3 scripts/tts_seed_audio.py --shots S00,S01      # try a couple of shots first
  python3 scripts/tts_seed_audio.py                      # every shot
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NARRATION = ROOT / "docs" / "02-旁白稿.txt"
OUT_DIR = ROOT / "public" / "audio" / "vo"
CACHE_DIR = ROOT / ".cache" / "tts"
DEFAULT_URL = "https://openspeech.bytedance.com/api/v3/tts/create"
DEFAULT_SPEAKER = "zh_male_m191_uranus_bigtts"

VOICE = ("中年男性，普通话，嗓音低沉浑厚、略带沙哑，语气克制、带着悬念，"
         "像在深夜讲一个西部决斗的故事，语速偏慢，在破折号和省略号处明显停顿")
# Shots that should be delivered almost under the breath (see docs/02-文案.md).
QUIET = {"S08", "S16"}


def load_lines():
    lines = []
    for raw in NARRATION.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            shot, text = raw.split("|", 1)
            lines.append((shot.strip(), text.strip()))
    return lines


def build_body(shot, text, speaker, speech_rate):
    voice = VOICE + ("，这一句声音压低，几乎是低语" if shot in QUIET else "")
    ref = "（音色参考 @audio1）" if speaker else ""
    prompt = (f"旁白{ref}（{voice}）说道：“{text}” "
              "只有干净的人声，没有背景音乐，没有音效，没有环境声。")
    body = {
        "model": "seed-audio-1.0",
        "text_prompt": prompt,
        "audio_config": {
            "format": "mp3",
            "sample_rate": 48000,
            "pitch_rate": 0,
            "speech_rate": speech_rate,
            "loudness_rate": 0,
        },
    }
    if speaker:
        body["references"] = [{"speaker": speaker}]
    return body


def auth_headers():
    api_key = os.environ.get("VOLC_TTS_API_KEY")
    if api_key:
        return {"X-Api-Key": api_key}
    app_id = os.environ.get("VOLC_TTS_APP_ID")
    token = os.environ.get("VOLC_TTS_ACCESS_TOKEN")
    if app_id and token:
        return {"X-Api-App-Id": app_id, "X-Api-Access-Key": token}
    sys.exit("Set VOLC_TTS_API_KEY (or VOLC_TTS_APP_ID + VOLC_TTS_ACCESS_TOKEN) first.")


def find_audio(node):
    """Return ("url", value) or ("b64", value) from an unknown response shape."""
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                if value.startswith("http") and re.search(r"url|location|audio", key, re.I):
                    return "url", value
                if len(value) > 1000 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", value[:2000]):
                    return "b64", value
            found = find_audio(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = find_audio(item)
            if found:
                return found
    return None


def call(url, body):
    headers = {"Content-Type": "application/json", "X-Api-Request-Id": str(uuid.uuid4())}
    headers.update(auth_headers())
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        sys.exit(f"HTTP {err.code}: {err.read().decode(errors='replace')[:500]}")
    except urllib.error.URLError as err:
        sys.exit(f"Cannot reach {url}: {err.reason} (is the host allowed by the network policy?)")


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", help="comma-separated shot ids, e.g. S00,S01")
    ap.add_argument("--dry-run", action="store_true", help="print the request body and stop")
    args = ap.parse_args()

    speaker = os.environ.get("VOICE_SPEAKER", DEFAULT_SPEAKER)
    speech_rate = int(os.environ.get("SPEECH_RATE", "0"))
    url = os.environ.get("VOLC_TTS_URL", DEFAULT_URL)
    wanted = set(args.shots.split(",")) if args.shots else None
    lines = [(s, t) for s, t in load_lines() if wanted is None or s in wanted]

    if args.dry_run:
        shot, text = lines[0]
        print(f"POST {url}")
        print(json.dumps(build_body(shot, text, speaker, speech_rate), ensure_ascii=False, indent=2))
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    durations_path = OUT_DIR / "durations.json"
    durations = json.loads(durations_path.read_text()) if durations_path.exists() else {}

    for shot, text in lines:
        resp = call(url, build_body(shot, text, speaker, speech_rate))
        found = find_audio(resp)
        if not found:
            (CACHE_DIR / f"{shot}.json").write_text(json.dumps(resp, ensure_ascii=False, indent=2))
            sys.exit(f"{shot}: no audio in response, saved to .cache/tts/{shot}.json")
        kind, value = found
        target = OUT_DIR / f"{shot}.mp3"
        if kind == "url":
            urllib.request.urlretrieve(value, target)
        else:
            target.write_bytes(base64.b64decode(value))
        durations[shot] = duration(target)
        print(f"{shot} {durations[shot]:5.2f}s  {text}")

    durations_path.write_text(json.dumps(dict(sorted(durations.items())), indent=2) + "\n")
    print(f"total {sum(durations.values()):.1f}s -> {durations_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

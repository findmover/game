"""Estimate narration length per shot from docs/02-旁白稿.txt.

Uses a slow, dramatic Mandarin pace plus pauses for punctuation. The real
timing gets recalibrated against the recorded voiceover in step 4.
"""
import re
from pathlib import Path

RATE = 4.3  # Chinese characters per second

path = Path(__file__).resolve().parent.parent / "docs" / "02-旁白稿.txt"
total_chars = total_secs = 0
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    shot, text = line.split("|", 1)
    chars = len(re.findall(r"[一-鿿0-9]", text))
    pauses = (len(re.findall(r"[，、：]", text)) * 0.25
              + len(re.findall(r"[。？！]", text)) * 0.45
              + len(re.findall(r"——|……", text)) * 0.5)
    secs = chars / RATE + pauses
    total_chars += chars
    total_secs += secs
    print(f"{shot} {chars:3d}字 ~{secs:4.1f}s")
print(f"合计 {total_chars} 字，旁白约 {total_secs:.0f}s")

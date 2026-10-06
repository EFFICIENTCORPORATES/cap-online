#!/usr/bin/env python3
"""Create raw + Roman-script transcripts from a short audio test clip."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from faster_whisper import WhisperModel
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")


def romanize_devanagari(text: str) -> str:
    """Romanize only Devanagari spans; preserve existing English/Hinglish tokens."""
    def repl(match: re.Match[str]) -> str:
        value = transliterate(match.group(0), sanscript.DEVANAGARI, sanscript.ITRANS)
        # Make ITRANS a little easier to read while keeping it deterministic.
        return (
            value.replace("A", "aa")
            .replace("I", "ee")
            .replace("U", "oo")
            .replace("RRi", "ri")
            .replace("R^i", "ri")
            .replace("M", "n")
            .replace("H", "h")
            .replace("~N", "n")
            .replace("~n", "n")
        )

    return DEVANAGARI_RE.sub(repl, text)


def timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio")
    parser.add_argument("output_dir")
    parser.add_argument("--model", default="small")
    parser.add_argument("--window-seconds", type=int, default=5)
    args = parser.parse_args()

    audio = Path(args.audio)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4)
    segments, info = model.transcribe(
        str(audio),
        language=None,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=True,
        initial_prompt=(
            "CA Intermediate Advanced Accounting lecture. The speaker uses Hindi, English "
            "and Hinglish. Preserve English accounting terminology such as ICAI, Accounting "
            "Standards, AS 10, property plant and equipment, recognition, measurement, "
            "depreciation, impairment, cost, carrying amount, journal entry, debit and credit."
        ),
    )

    words = []
    raw_segments = []
    for seg in segments:
        seg_words = []
        for w in seg.words or []:
            if w.start is None or w.end is None:
                continue
            item = {
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
                "word": w.word,
                "probability": round(float(w.probability), 5),
            }
            words.append(item)
            seg_words.append(item)
        raw_segments.append(
            {
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
                "romanized_text": romanize_devanagari(seg.text.strip()),
                "words": seg_words,
            }
        )

    duration = max([w["end"] for w in words], default=0.0)
    windows = []
    for i in range(int(math.ceil(duration / args.window_seconds))):
        start = i * args.window_seconds
        end = (i + 1) * args.window_seconds
        tokens = [w["word"] for w in words if start <= w["start"] < end]
        raw = " ".join(x.strip() for x in tokens if x.strip())
        raw = re.sub(r"\s+([,.;:!?])", r"\1", raw).strip()
        windows.append(
            {
                "start": start,
                "end": end,
                "raw_text": raw,
                "romanized_text": romanize_devanagari(raw),
            }
        )

    meta = {
        "model": args.model,
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "window_seconds": args.window_seconds,
        "audio_file": audio.name,
    }
    payload = {"metadata": meta, "windows": windows, "segments": raw_segments}
    (out / "transcript.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    raw_md = [
        "# Raw Whisper Transcript",
        "",
        f"- Model: {args.model}",
        f"- Detected language: {info.language}",
        f"- Language probability: {info.language_probability:.4f}",
        "",
    ]
    roman_md = [
        "# Romanized Transcript",
        "",
        "This file converts Devanagari spans to Roman characters while preserving English words.",
        "",
    ]
    roman_txt = []

    for w in windows:
        if not w["raw_text"]:
            continue
        stamp = f"[{timestamp(w['start'])} - {timestamp(w['end'])}]"
        raw_md.append(f"**{stamp}** {w['raw_text']}")
        raw_md.append("")
        roman_md.append(f"**{stamp}** {w['romanized_text']}")
        roman_md.append("")
        roman_txt.append(f"{stamp} {w['romanized_text']}")

    (out / "transcript-raw.md").write_text("\n".join(raw_md) + "\n", encoding="utf-8")
    (out / "transcript-romanized.md").write_text("\n".join(roman_md) + "\n", encoding="utf-8")
    (out / "transcript-romanized.txt").write_text("\n".join(roman_txt) + "\n", encoding="utf-8")

    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()

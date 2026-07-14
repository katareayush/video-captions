#!/usr/bin/env python3
"""Transcribe a video's speech to word-timestamped segments using faster-whisper.

faster-whisper decodes the audio itself (via bundled PyAV), so ffmpeg is NOT required for
this step. Output is a JSON file: {"language": str, "segments": [{text, start, end, words}]}
with times in seconds.
"""
import json
import sys
from pathlib import Path


def transcribe(video, model_size="base", out_path="segments.json", language=None, translate=False):
    """language: source language code (None = auto-detect).
    translate: if True, output English captions for any spoken language (Whisper translate task).
    """
    from faster_whisper import WhisperModel

    # int8 keeps CPU usage/RAM low and is plenty accurate for captions.
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        str(video),
        word_timestamps=True,
        vad_filter=True,  # skip long silences -> tighter timing
        language=language,
        task="translate" if translate else "transcribe",
    )

    out_segments = []
    for seg in segments:  # generator: iterating drives the actual work
        words = []
        for w in (seg.words or []):
            text = (w.word or "").strip()
            if text and w.start is not None and w.end is not None:
                words.append({"text": text, "start": w.start, "end": w.end})
        out_segments.append(
            {
                "text": (seg.text or "").strip(),
                "start": seg.start,
                "end": seg.end,
                "words": words,
            }
        )

    Path(out_path).write_text(
        json.dumps(
            {"language": info.language, "segments": out_segments},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return out_path


if __name__ == "__main__":
    video = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    out = sys.argv[3] if len(sys.argv) > 3 else "segments.json"
    transcribe(video, model_size, out)
    print(f"Wrote {out}")

#!/usr/bin/env python3
"""Locate an ffmpeg build that can actually render subtitles (has libass).

Homebrew's default `ffmpeg` on macOS is now a slim build WITHOUT libass, so the `subtitles`
filter is missing. `ffmpeg-full` provides it but is keg-only. Windows (gyan.dev/BtbN) and
Linux (apt) ffmpeg builds include libass already. This picks the right binary automatically.
"""
import shutil
import subprocess
from pathlib import Path

# keg-only full builds on macOS (Apple Silicon and Intel Homebrew prefixes)
FULL_CANDIDATES = [
    "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
    "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
]


def _has_subtitles(ffmpeg):
    try:
        out = subprocess.run(
            [ffmpeg, "-hide_banner", "-filters"],
            capture_output=True, text=True,
        ).stdout
        return "subtitles" in out
    except Exception:
        return False


def _sibling(ffmpeg, name):
    """ffprobe path next to an ffmpeg binary, preserving any .exe suffix."""
    p = Path(ffmpeg)
    return str(p.with_name(p.name.replace("ffmpeg", name)))


def find_ffmpeg():
    """Return (ffmpeg, ffprobe) with libass support, or (None, None) if none found."""
    candidates = []
    on_path = shutil.which("ffmpeg")
    if on_path:
        candidates.append(on_path)
    candidates += [c for c in FULL_CANDIDATES if Path(c).exists()]

    for ff in candidates:
        if _has_subtitles(ff):
            probe = _sibling(ff, "ffprobe")
            return ff, (probe if Path(probe).exists() else (shutil.which("ffprobe") or "ffprobe"))
    return None, None

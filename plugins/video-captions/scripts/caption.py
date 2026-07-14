#!/usr/bin/env python3
"""Orchestrator: video in -> captioned video out.

Runs transcribe -> build_captions -> ffmpeg burn. Cross-platform (Windows/macOS/Linux):
uses pathlib for paths and runs ffmpeg with the caption file as a bare relative name from the
work directory, which sidesteps the Windows `subtitles=C:\\...` colon/backslash escaping bug.

The look is minimal and common by default; every aspect is overridable via flags so the
caller (Claude) can translate a user's freeform description ("big yellow text at the top")
into concrete styling.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ffmpeg_tools import find_ffmpeg

# Minimal, common baseline (clean white subtitles). Overridden by flags per the user's prompt.
DEFAULT_STYLE = {
    "font": "Arial",
    "size_ratio": 0.05,   # font height as a fraction of video height
    "primary": "FFFFFF",  # text colour (RRGGBB)
    "outline_color": "000000",
    "outline": 2,         # outline width
    "shadow": 1,          # shadow depth
    "bold": False,
}

COLORS = {
    "white": "FFFFFF", "black": "000000", "yellow": "FFFF00", "red": "FF0000",
    "green": "00FF00", "blue": "0000FF", "cyan": "00FFFF", "magenta": "FF00FF",
    "orange": "FFA500", "pink": "FF69B4", "purple": "800080", "gray": "808080",
    "grey": "808080",
}
SIZES = {"small": 0.042, "medium": 0.052, "large": 0.072, "huge": 0.095}


def probe_dimensions(ffprobe, video):
    """Return (width, height) via ffprobe; fall back to 1280x720 if unavailable."""
    try:
        out = subprocess.run(
            [
                ffprobe, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "json", str(video),
            ],
            capture_output=True, text=True, check=True,
        ).stdout
        stream = json.loads(out)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except Exception:
        return 1280, 720


def parse_color(value):
    v = value.strip().lstrip("#")
    if len(v) == 6 and all(c in "0123456789abcdefABCDEF" for c in v):
        return v.upper()
    if v.lower() in COLORS:
        return COLORS[v.lower()]
    sys.exit(f"Unknown color '{value}'. Use a hex like FFCC00 or a name: {', '.join(COLORS)}")


def parse_size(value):
    if value.lower() in SIZES:
        return SIZES[value.lower()]
    try:
        return float(value)
    except ValueError:
        sys.exit("--size must be small|medium|large|huge or a number like 0.05")


def build_style(args):
    """Start from the minimal baseline; apply only what the caller specified."""
    style = dict(DEFAULT_STYLE)
    if args.font:
        style["font"] = args.font
    if args.size:
        style["size_ratio"] = parse_size(args.size)
    if args.color:
        style["primary"] = parse_color(args.color)
    if args.outline_color:
        style["outline_color"] = parse_color(args.outline_color)
    if args.outline is not None:
        style["outline"] = args.outline
    if args.shadow is not None:
        style["shadow"] = args.shadow
    if args.weight:
        style["bold"] = args.weight == "bold"
    return style


def main():
    ap = argparse.ArgumentParser(description="Transcribe a video and burn in captions.")
    ap.add_argument("video", help="path to the input video")
    ap.add_argument("--pos", default="bottom", choices=["top", "center", "bottom"])
    ap.add_argument("--model", default="base", help="whisper model (base, small, ...)")
    ap.add_argument("--out", default=None, help="output path (default: <name>_captioned.mp4)")
    # style overrides — Claude fills these from the user's freeform description
    ap.add_argument("--font", help="font family, e.g. Arial, Impact, Georgia")
    ap.add_argument("--size", help="small|medium|large|huge or a ratio like 0.06")
    ap.add_argument("--color", help="text colour: a name (yellow) or hex (FFCC00)")
    ap.add_argument("--outline-color", dest="outline_color", help="outline colour (name or hex)")
    ap.add_argument("--outline", type=float, help="outline width (0 for none)")
    ap.add_argument("--shadow", type=float, help="shadow depth (0 for none)")
    ap.add_argument("--weight", choices=["bold", "normal"], help="text weight")
    args = ap.parse_args()

    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        sys.exit(f"Video not found: {video}")

    ffmpeg, ffprobe = find_ffmpeg()
    if ffmpeg is None:
        sys.exit(
            "No ffmpeg with subtitle support found. Run: python scripts/setup.py\n"
            "(macOS: `brew install ffmpeg-full`; Windows/Linux: install ffmpeg.)"
        )

    out = (
        Path(args.out).expanduser().resolve()
        if args.out
        else video.with_name(video.stem + "_captioned.mp4")
    )

    work = Path(tempfile.mkdtemp(prefix="vidcap_"))
    seg_path = work / "segments.json"
    ass_name = "captions.ass"  # kept relative for the ffmpeg subtitles filter
    ass_path = work / ass_name

    # 1) transcribe (first run downloads the model)
    from transcribe import transcribe
    print("Transcribing speech (first run downloads the model)...")
    transcribe(video, args.model, seg_path)

    # 2) build well-timed, well-placed captions with the requested look
    from build_captions import build
    width, height = probe_dimensions(ffprobe, video)
    build(seg_path, ass_path, width, height, build_style(args), pos=args.pos)

    # 3) burn into the video (run from work dir so the filter sees a bare filename)
    print("Burning captions into the video...")
    subprocess.run(
        [
            ffmpeg, "-y", "-i", str(video),
            "-vf", f"subtitles={ass_name}",
            "-c:a", "copy", str(out),
        ],
        cwd=str(work),
        check=True,
    )

    print(f"Done -> {out}")


if __name__ == "__main__":
    main()

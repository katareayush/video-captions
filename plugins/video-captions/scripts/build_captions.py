#!/usr/bin/env python3
"""Turn word-timestamped segments into a well-placed, well-timed .ass subtitle file.

This is the heart of the skill. The goal is captions that:
  - are chunked into short, readable lines (no wall of text),
  - appear/disappear in sync with the speech (from word timestamps),
  - stay on screen long enough to read but do not linger or overlap,
  - are positioned and outlined so they read over any footage.

Stdlib only.
"""
import json
import sys
from pathlib import Path

# --- tuning knobs -----------------------------------------------------------
MAX_CHARS_PER_LINE = 42   # readable line length
MAX_LINES = 2             # at most two lines per caption
MAX_GAP = 0.7             # a pause longer than this starts a new caption
MAX_DURATION = 6.0        # never keep one caption up longer than this
MIN_DURATION = 1.0        # minimum on-screen time so captions are readable
INTER_GAP = 0.05          # small gap between captions to avoid flicker/overlap


def to_ass_color(hex_rgb, alpha=0):
    """#RRGGBB -> ASS &HAABBGGRR (BGR order, alpha 0x00 = opaque)."""
    hex_rgb = hex_rgb.lstrip("#")
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def fmt_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def flatten_words(segments):
    """All words in order. Falls back to whole-segment chunks if a segment lacks words."""
    words = []
    for seg in segments:
        seg_words = seg.get("words") or []
        if seg_words:
            words.extend(
                {"text": w["text"], "start": w["start"], "end": w["end"]}
                for w in seg_words
            )
        elif seg.get("text"):
            words.append(
                {"text": seg["text"].strip(), "start": seg["start"], "end": seg["end"]}
            )
    return words


def chunk_words(words):
    """Group consecutive words into caption-sized chunks."""
    max_total = MAX_CHARS_PER_LINE * MAX_LINES
    chunks, cur = [], []

    def cur_len():
        return sum(len(w["text"]) for w in cur) + max(0, len(cur) - 1)

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            dur = w["end"] - cur[0]["start"]
            prospective = cur_len() + 1 + len(w["text"])
            if prospective > max_total or gap > MAX_GAP or dur > MAX_DURATION:
                chunks.append(cur)
                cur = []
        cur.append(w)
        # break after sentence-ending punctuation for natural boundaries
        if w["text"][-1:] in ".!?":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def wrap_lines(text):
    """Wrap a caption's text into at most MAX_LINES lines using \\N."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        if cur and len(cur) + 1 + len(word) > MAX_CHARS_PER_LINE:
            lines.append(cur)
            cur = word
        else:
            cur = word if not cur else f"{cur} {word}"
    if cur:
        lines.append(cur)
    if len(lines) > MAX_LINES:  # rare overflow: merge remainder into the last allowed line
        lines = lines[: MAX_LINES - 1] + [" ".join(lines[MAX_LINES - 1:])]
    return "\\N".join(lines)


def build(seg_path, ass_path, width, height, style, pos="bottom"):
    data = json.loads(Path(seg_path).read_text(encoding="utf-8"))
    chunks = [c for c in chunk_words(flatten_words(data["segments"])) if c]

    alignment = {"bottom": 2, "center": 5, "top": 8}[pos]
    margin_v = int(height * 0.06)
    fontsize = max(16, int(height * style["size_ratio"]))
    bold = -1 if style.get("bold") else 0
    primary = to_ass_color(style["primary"])
    outline_c = to_ass_color(style["outline_color"])
    back_c = to_ass_color("000000", alpha=0x80)

    events = []
    for i, chunk in enumerate(chunks):
        start = chunk[0]["start"]
        end = chunk[-1]["end"]
        if end - start < MIN_DURATION:
            end = start + MIN_DURATION
        if i + 1 < len(chunks):  # don't overlap the next caption
            next_start = chunks[i + 1][0]["start"]
            if end > next_start - INTER_GAP:
                end = max(start + 0.4, next_start - INTER_GAP)
        text = wrap_lines(" ".join(w["text"] for w in chunk))
        events.append((start, end, text))

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{style['font']},{fontsize},{primary},&H000000FF,{outline_c},"
        f"{back_c},{bold},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},"
        f"{alignment},60,60,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    lines = [header]
    for start, end, text in events:
        lines.append(
            f"Dialogue: 0,{fmt_time(start)},{fmt_time(end)},Default,,0,0,0,,{text}"
        )
    Path(ass_path).write_text("\n".join(lines), encoding="utf-8")
    return ass_path


if __name__ == "__main__":
    # build_captions.py segments.json out.ass WIDTH HEIGHT [pos]
    default_style = {
        "font": "Arial",
        "size_ratio": 0.05,
        "primary": "FFFFFF",
        "outline_color": "000000",
        "outline": 2,
        "shadow": 1,
        "bold": False,
    }
    build(
        sys.argv[1],
        sys.argv[2],
        int(sys.argv[3]),
        int(sys.argv[4]),
        default_style,
        pos=sys.argv[5] if len(sys.argv) > 5 else "bottom",
    )
    print(f"Wrote {sys.argv[2]}")

#!/usr/bin/env python3
"""Turn word-timestamped segments into captions and render them.

The heart of the skill. Produces caption *events* (short, readable, synced lines) from raw
word timestamps, then renders them to:
  - ASS   (for burning into the video, with optional styling / box / word-by-word highlight)
  - SRT / VTT (editable sidecar files)

Also parses an existing SRT back into events (edit-then-burn). Stdlib only.
"""
import json
import re
import sys
from pathlib import Path

# --- tuning knobs -----------------------------------------------------------
MAX_CHARS_PER_LINE = 42
MAX_LINES = 2
MAX_GAP = 0.7
MAX_DURATION = 6.0
MIN_DURATION = 1.0
INTER_GAP = 0.05
WBW_GROUP = 4        # words shown at once in word-by-word mode
WBW_GAP = 0.5        # a pause longer than this starts a new word-by-word group


# --- colour / time helpers --------------------------------------------------
def to_ass_color(hex_rgb, alpha=0):
    """#RRGGBB -> ASS &HAABBGGRR (BGR, alpha 0x00 = opaque)."""
    hex_rgb = hex_rgb.lstrip("#")
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def srt_time(t, sep=","):
    t = max(0.0, t)
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        ms = 0; s += 1
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


# --- words -> events --------------------------------------------------------
def flatten_words(segments):
    words = []
    for seg in segments:
        seg_words = seg.get("words") or []
        if seg_words:
            words.extend({"text": w["text"], "start": w["start"], "end": w["end"]} for w in seg_words)
        elif seg.get("text"):
            words.append({"text": seg["text"].strip(), "start": seg["start"], "end": seg["end"]})
    return words


def _chunk(words, max_total, max_words, max_gap):
    chunks, cur = [], []

    def cur_len():
        return sum(len(w["text"]) for w in cur) + max(0, len(cur) - 1)

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            dur = w["end"] - cur[0]["start"]
            too_long = cur_len() + 1 + len(w["text"]) > max_total or len(cur) >= max_words
            if too_long or gap > max_gap or dur > MAX_DURATION:
                chunks.append(cur); cur = []
        cur.append(w)
        if w["text"][-1:] in ".!?":
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    return chunks


def _wrap(text, max_chars=MAX_CHARS_PER_LINE, max_lines=MAX_LINES):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur); cur = word
        else:
            cur = word if not cur else f"{cur} {word}"
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [" ".join(lines[max_lines - 1:])]
    return "\n".join(lines)


def line_events(segments):
    """Normal captions: short wrapped lines synced to speech. Returns [{start,end,text}]."""
    chunks = [c for c in _chunk(flatten_words(segments), MAX_CHARS_PER_LINE * MAX_LINES, 99, MAX_GAP) if c]
    events = []
    for i, chunk in enumerate(chunks):
        start, end = chunk[0]["start"], chunk[-1]["end"]
        if end - start < MIN_DURATION:
            end = start + MIN_DURATION
        if i + 1 < len(chunks):
            nxt = chunks[i + 1][0]["start"]
            if end > nxt - INTER_GAP:
                end = max(start + 0.4, nxt - INTER_GAP)
        events.append({"start": start, "end": end, "text": _wrap(" ".join(w["text"] for w in chunk))})
    return events


# --- renderers --------------------------------------------------------------
def _ass_header(width, height, style, alignment, margin_v, box):
    fontsize = max(16, int(height * style["size_ratio"]))
    bold = -1 if style.get("bold") else 0
    primary = to_ass_color(style["primary"])
    if box:
        border_style = 3                       # opaque box behind text
        outline = max(4, int(style.get("outline", 2)))
        outline_c = to_ass_color(style.get("box_color", "000000"), alpha=0x40)
        shadow = 0
    else:
        border_style = 1                       # outline + shadow
        outline = style.get("outline", 2)
        outline_c = to_ass_color(style["outline_color"])
        shadow = style.get("shadow", 1)
    back_c = to_ass_color("000000", alpha=0x80)
    return (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{style['font']},{fontsize},{primary},&H000000FF,{outline_c},"
        f"{back_c},{bold},0,0,0,100,100,0,0,{border_style},{outline},{shadow},"
        f"{alignment},60,60,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def render_ass(events, width, height, style, pos="bottom", box=False):
    alignment = {"bottom": 2, "center": 5, "top": 8}[pos]
    margin_v = int(height * 0.06)
    out = [_ass_header(width, height, style, alignment, margin_v, box)]
    for e in events:
        out.append(f"Dialogue: 0,{ass_time(e['start'])},{ass_time(e['end'])},Default,,0,0,0,,"
                   + e["text"].replace("\n", "\\N"))
    return "\n".join(out)


def render_word_by_word(segments, width, height, style, pos="center", highlight="FFFF00"):
    """Viral / karaoke look: a few words on screen, the spoken word highlighted."""
    alignment = {"bottom": 2, "center": 5, "top": 8}[pos]
    margin_v = int(height * 0.06)
    hl = to_ass_color(highlight)
    groups = [g for g in _chunk(flatten_words(segments), 9999, WBW_GROUP, WBW_GAP) if g]
    out = [_ass_header(width, height, style, alignment, margin_v, box=False)]
    for group in groups:
        group_end = group[-1]["end"]
        for j, w in enumerate(group):
            start = w["start"]
            end = group[j + 1]["start"] if j + 1 < len(group) else group_end
            if end <= start:
                end = start + 0.1
            parts = []
            for k, ww in enumerate(group):
                if k == j:
                    parts.append("{\\c" + hl + "&}{\\fscx112\\fscy112}" + ww["text"] + "{\\r}")
                else:
                    parts.append(ww["text"])
            out.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,"
                       + " ".join(parts))
    return "\n".join(out)


def render_srt(events):
    out = []
    for i, e in enumerate(events, 1):
        out += [str(i), f"{srt_time(e['start'])} --> {srt_time(e['end'])}", e["text"], ""]
    return "\n".join(out)


def render_vtt(events):
    out = ["WEBVTT", ""]
    for e in events:
        out += [f"{srt_time(e['start'], '.')} --> {srt_time(e['end'], '.')}", e["text"], ""]
    return "\n".join(out)


# --- SRT -> events (edit-then-burn) -----------------------------------------
_SRT_TIME = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})")


def _parse_time(s):
    m = _SRT_TIME.search(s)
    if not m:
        return None
    h, mi, se, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(se) + int(ms.ljust(3, "0")) / 1000


def parse_srt(path):
    """Read an .srt/.vtt back into [{start,end,text}] so a corrected file can be re-burned."""
    text = Path(path).read_text(encoding="utf-8-sig")
    events = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        time_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if time_idx is None:
            continue
        a, _, b = lines[time_idx].partition("-->")
        start, end = _parse_time(a), _parse_time(b)
        if start is None or end is None:
            continue
        body = "\n".join(lines[time_idx + 1:]).strip()
        if body:
            events.append({"start": start, "end": end, "text": body})
    return events


if __name__ == "__main__":
    # build_captions.py segments.json out.ass WIDTH HEIGHT [pos]
    default_style = {"font": "Arial", "size_ratio": 0.05, "primary": "FFFFFF",
                     "outline_color": "000000", "outline": 2, "shadow": 1, "bold": False}
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ass = render_ass(line_events(data["segments"]), int(sys.argv[3]), int(sys.argv[4]),
                     default_style, pos=sys.argv[5] if len(sys.argv) > 5 else "bottom")
    Path(sys.argv[2]).write_text(ass, encoding="utf-8")
    print(f"Wrote {sys.argv[2]}")

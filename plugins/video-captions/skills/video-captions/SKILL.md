---
name: video-captions
description: Add burned-in captions to a video by transcribing its speech locally and placing the text in sync. The caption look defaults to a minimal, common style, but the user can describe any design in plain words and it will be applied. Use when the user wants to caption or subtitle a video file. Works offline on Windows and macOS. Trigger phrases: "add captions", "add subtitles", "caption this video".
---

# video-captions

Transcribes a video's speech (locally, via faster-whisper) and burns accurately-timed
captions into it (via ffmpeg). Offline after a one-time model download. No API key.
Default look is clean/minimal; the user can describe any style and you apply it.

## Do this — two commands

Use `python3` on macOS/Linux, `python` on Windows. The scripts live at
`${CLAUDE_PLUGIN_ROOT}/scripts/` — always call them by that path (the working directory is the
user's project, not this plugin).

**1. First time only — install (one command):**
```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py"
```
Installs faster-whisper and, on macOS, an ffmpeg build with subtitle support. Idempotent.

**2. Every time — caption a video (one command):**
```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/caption.py" "<path/to/video>"
```
Writes `<name>_captioned.mp4` next to the input. With no style flags it uses a minimal,
common look (clean white subtitles, thin outline, bottom-centre). Report the output path.

The first caption run downloads the Whisper model once (a few hundred MB); afterwards it's fully offline.

## The user describes the design — you translate it into flags

There are no fixed presets. If the user describes a look, map their words to these flags
(pass only the ones they implied; leave the rest at the minimal default):

- `--pos top|center|bottom`
- `--color <name|hex>`  (text colour: `yellow`, `FFCC00`, ...)
- `--outline-color <name|hex>`
- `--size small|medium|large|huge` (or a ratio like `0.06`)
- `--outline <n>`  (thickness; `0` = none)
- `--shadow <n>`   (depth; `0` = none)
- `--weight bold|normal`
- `--font <family>` (e.g. `Impact`, `Georgia`)
- `--out "<file>.mp4"`

## Transcribe accurately (do this so captions read correctly)

- **Context is the biggest lever.** If the user (or the request) mentions names, brands,
  products, or the topic, pass them so those words aren't misheard:
  `--context "Scrolt, Kubernetes, Ayush Katare, Grafana"`.
- **Model:** default `small` is accurate. Use `--model medium` or `--model large-v3` for tough
  audio, heavy accents, or when the user wants it perfect; `--model base` for a quick/light pass.
  If the user says words came out wrong, re-run one tier higher and/or add `--context`.
- **Language:** auto-detected. Force it with `--lang <code>` (e.g. `hi`, `es`) if detection is off.

Examples of mapping a description → command:
- "big bold yellow captions at the top" → `--pos top --size large --weight bold --color yellow`
- "clean minimal, no shadow" → `--shadow 0`
- "white text with a thick black outline" → `--color white --outline-color black --outline 4`
- "put them in the middle, nice and small" → `--pos center --size small`

If the user gives no style, run the bare command — do not ask.

## More capabilities (map these when asked)

- **Viral / TikTok style**: `--word-by-word` — a few words at a time, active word highlighted
  (defaults to big, bold, centred). Change the highlight with `--highlight <name|hex>`.
  ("make it TikTok style / karaoke / word by word" → `--word-by-word`)
- **Readability box**: `--box` (optional `--box-color <name|hex>`) — a band behind the text.
- **Any language / translation**: `--lang <code>` sets the spoken language (default: auto);
  `--translate` outputs English captions from any language.
- **Subtitle files**: `--export srt|vtt|both` writes an editable file next to the video;
  add `--no-burn` to skip rendering and only export.
- **Fix wrong words (edit-then-burn)**: export with `--export srt`, let the user correct the
  `.srt`, then burn the corrected file with `--from-srt "<file>.srt"` (no re-transcription).
- **Batch**: pass a folder instead of a file to caption every video in it.

Examples:
- "make it a viral TikTok caption" → `--word-by-word`
- "it's in Hindi, give me English subtitles" → `--translate`
- "just give me an SRT file" → `--export srt --no-burn`
- "caption all the videos in this folder" → pass the folder path

## Keep it cheap

Don't read the other files unless something fails — just run the command. Error messages say
exactly what to do (e.g. install ffmpeg).

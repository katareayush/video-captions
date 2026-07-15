# katareayush — Claude Code plugins

A Claude Code plugin marketplace. Currently hosts **video-captions**.

## video-captions

Give Claude a video and say *"add captions"* — it transcribes the speech **locally** and burns
accurately-timed captions into the video. The look defaults to a clean, minimal style, and you
can **describe any design in plain words** (*"big yellow captions at the top"*) and Claude
applies it. Fully offline after a one-time model download, cross-platform, no API key.

### Install (for anyone)

In Claude Code:

```
/plugin marketplace add katareayush/video-captions
/plugin install video-captions@katareayush
```

Then just say, in any project:

```
add captions to demo.mp4
```

The first run installs its dependencies (`faster-whisper` + a subtitle-capable `ffmpeg`) and
downloads the Whisper model once (~150 MB). Everything after is offline.

### Requirements

- **Python 3.9+**
- **ffmpeg** — the plugin's setup installs a subtitle-capable build automatically on macOS
  (`ffmpeg-full`); Windows/Linux ffmpeg already includes subtitle support.

### Describe the look

No rigid presets — describe what you want and Claude maps it to flags:

| You say | Claude runs |
|---------|-------------|
| (nothing) | clean white subtitles, bottom-centre |
| "big bold yellow captions at the top" | `--pos top --size large --weight bold --color yellow` |
| "white text, thick black outline" | `--color white --outline-color black --outline 4` |
| "minimal, no shadow" | `--shadow 0` |
| "a few words were wrong" | `--model small` |

Full flag reference is in [`plugins/video-captions/README.md`](plugins/video-captions/README.md).

## Repo layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog
└── plugins/
    └── video-captions/
        ├── .claude-plugin/plugin.json
        ├── README.md             # plugin docs + full flag reference
        ├── requirements.txt
        ├── scripts/              # setup, transcribe, build_captions, caption, ffmpeg_tools
        └── skills/video-captions/SKILL.md
```

## License

MIT — see [LICENSE](LICENSE).

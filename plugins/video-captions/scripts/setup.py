#!/usr/bin/env python3
"""One-shot, cross-platform setup for the video-captions skill.

Makes sure two things are ready:
  1. faster-whisper (pip)                -> speech-to-text
  2. an ffmpeg build WITH libass         -> burning styled subtitles

On macOS the default Homebrew `ffmpeg` lacks libass, so this installs `ffmpeg-full`
automatically. Windows/Linux ffmpeg builds already include libass.

The Whisper model downloads itself on first use, so there is nothing to fetch here.
Safe to run repeatedly.
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ffmpeg_tools import find_ffmpeg


def module_available(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def ensure_faster_whisper():
    if module_available("faster_whisper"):
        print("[ok] faster-whisper installed")
        return
    print("Installing faster-whisper (pip)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
        print("[ok] faster-whisper installed")
    except subprocess.CalledProcessError:
        print(f"[!!] Failed. Run manually: {sys.executable} -m pip install faster-whisper")


def ensure_ffmpeg():
    ffmpeg, _ = find_ffmpeg()
    if ffmpeg:
        print(f"[ok] ffmpeg with subtitle support: {ffmpeg}")
        return

    system = platform.system()
    if system == "Darwin" and shutil.which("brew"):
        print("ffmpeg is missing libass. Installing ffmpeg-full via Homebrew...")
        try:
            subprocess.run(["brew", "install", "ffmpeg-full"], check=True)
        except subprocess.CalledProcessError:
            print("[!!] brew install ffmpeg-full failed. Run it manually.")
        if find_ffmpeg()[0]:
            print("[ok] ffmpeg-full installed with subtitle support")
        else:
            print("[!!] Still no subtitle-capable ffmpeg found.")
        return

    hints = {
        "Darwin": "brew install ffmpeg-full",
        "Windows": "winget install Gyan.FFmpeg   (or: choco install ffmpeg-full)",
        "Linux": "sudo apt install ffmpeg",
    }
    print("[!!] No ffmpeg with subtitle support found. Install one:")
    print(f"     {hints.get(system, 'install a full ffmpeg build (with libass)')}")


def main():
    print(f"Python {sys.version.split()[0]} on {platform.system()}\n")
    ensure_faster_whisper()
    ensure_ffmpeg()
    print("\nReady. The Whisper model downloads automatically the first time you caption a video.")


if __name__ == "__main__":
    main()

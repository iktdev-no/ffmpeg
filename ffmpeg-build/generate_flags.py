#!/usr/bin/env python3
import json
from pathlib import Path
from typing import List

CONFIG_PATH = Path("ffmpeg-build/config/gpu-backends.json")
OUTPUT_PATH = Path("ffmpeg-build/generated-flags.txt")

def main():
    config = json.loads(CONFIG_PATH.read_text())
    flags: List[str] = []

    if config["cpu"]["enabled"]:
        flags += config["cpu"].get("ffmpegFlags", [])

    for backend in config["amd"].values():
        if backend["enabled"]:
            flags += backend.get("ffmpegFlags", [])

    for backend in config["nvidia"].values():
        if backend["enabled"]:
            flags += backend.get("ffmpegFlags", [])

    for backend in config["intel"].values():
        if backend["enabled"]:
            flags += backend.get("ffmpegFlags", [])

    OUTPUT_PATH.write_text("\n".join(flags))

    print("Generated FFmpeg flags:")
    for f in flags:
        print(f)

if __name__ == "__main__":
    main()

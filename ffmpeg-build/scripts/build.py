#!/usr/bin/env python3
import subprocess
from pathlib import Path
from typing import List

FLAGS_PATH = Path("ffmpeg-build/generated-flags.txt")
DIST_PATH = Path("ffmpeg-build/dist")

def run(cmd: List[str]):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    DIST_PATH.mkdir(exist_ok=True)

    # Clone FFmpeg
    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"])

    # Configure
    flags = FLAGS_PATH.read_text().replace("\n", " ")
    run(["bash", "-c", f"cd ffmpeg && ./configure {flags}"])

    # Build (verbose)
    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"])

    # Copy binaries
    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH)])
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH)])

if __name__ == "__main__":
    main()

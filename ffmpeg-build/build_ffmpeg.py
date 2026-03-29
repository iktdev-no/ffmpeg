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
    DIST_PATH.mkdir(parents=True, exist_ok=True)

    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "pkg-config"])

    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"])

    flags = FLAGS_PATH.read_text().replace("\n", " ")
    cfg = f"./configure {flags} --prefix=/usr/local"

    run(["bash", "-c", f"cd ffmpeg && {cfg}"])
    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"])

    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH / "ffmpeg")])
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH / "ffprobe")])

if __name__ == "__main__":
    main()

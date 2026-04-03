#!/usr/bin/env python3
import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict

FLAGS_PATH = Path("ffmpeg-build/generated-flags.txt")
DIST_PATH = Path("ffmpeg-build/dist")

def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, env=env)

def main() -> None:
    DIST_PATH.mkdir(parents=True, exist_ok=True)

    env: Dict[str, str] = os.environ.copy()

    # (valgfritt, men trygt å beholde)
    env["CFLAGS"] = "-I/usr/local/include"
    env["LDFLAGS"] = "-L/usr/local/lib"

    run(["sudo", "apt-get", "update"], env=env)
    run(["sudo", "apt-get", "install", "-y",
         "git",
         "nasm",
         "yasm"
    ], env=env)

    # clean clone (viktig i CI-cache scenario)
    run(["rm", "-rf", "ffmpeg"], env=env)
    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"], env=env)

    flags = FLAGS_PATH.read_text().replace("\n", " ").strip()

    cfg = (
        f"./configure {flags} "
        "--prefix=/usr/local "
        "--enable-static "
        "--disable-shared "
        "--extra-cflags='-I/usr/local/include' "
        "--extra-ldflags='-L/usr/local/lib "
        "-lx264 -lx265 -laom -lvpx -lSvtAv1Enc "
        "-lpthread -lm -lz -ldl'"
    )

    # run configure
    run(["bash", "-c", f"cd ffmpeg && {cfg}"], env=env)

    # build
    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"], env=env)

    # install artifacts
    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH / "ffmpeg")], env=env)
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH / "ffprobe")], env=env)

if __name__ == "__main__":
    main()
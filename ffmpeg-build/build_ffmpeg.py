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
    env["PKG_CONFIG_PATH"] = "/usr/local/lib/pkgconfig"
    env["PKG_CONFIG_LIBDIR"] = "/usr/local/lib/pkgconfig"
    env["CFLAGS"] = "-I/usr/local/include"
    env["LDFLAGS"] = "-L/usr/local/lib"

    run(["sudo", "apt-get", "update"], env=env)
    run(["sudo", "apt-get", "install", "-y",
         "git",
         "pkg-config",
         "nasm",
         "yasm"
    ], env=env)

    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"], env=env)

    flags = FLAGS_PATH.read_text().replace("\n", " ")
    cfg = f"./configure {flags} --prefix=/usr/local"

    # ⭐ FIX: FORCE PKG_CONFIG_PATH INSIDE THE CONFIGURE COMMAND
    run([
        "bash", "-c",
        f"cd ffmpeg && PKG_CONFIG_PATH=/usr/local/lib/pkgconfig PKG_CONFIG_LIBDIR=/usr/local/lib/pkgconfig {cfg}"
    ], env=env)

    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"], env=env)

    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH / "ffmpeg")], env=env)
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH / "ffprobe")], env=env)

if __name__ == "__main__":
    main()

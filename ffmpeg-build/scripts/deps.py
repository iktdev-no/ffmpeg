#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from typing import List

CONFIG_PATH = Path("ffmpeg-build/config/gpu-backends.json")

def run(cmd: List[str]):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

def install_packages(packages: List[str]):
    if not packages:
        return
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y"] + packages)

def main():
    # Core FFmpeg deps
    install_packages([
        "nasm",
        "yasm",
        "pkg-config",
        "build-essential",
        "libx264-dev",
        "libx265-dev",
        "libvpx-dev",
        "libaom-dev",
        "libdrm-dev",
        "libsvtav1-dev"
    ])

    config = json.loads(CONFIG_PATH.read_text())

    # AMD VAAPI
    for backend in config["amd"].values():
        if backend["enabled"]:
            install_packages(backend.get("packages", []))

    # NVIDIA (no deps in CI)

    # Intel VAAPI (QSV disabled)
    for backend in config["intel"].values():
        if backend["enabled"]:
            install_packages(backend.get("packages", []))

if __name__ == "__main__":
    main()

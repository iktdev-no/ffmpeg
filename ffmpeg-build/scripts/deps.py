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

def build_svt_av1():
    # Install build tools
    install_packages([
        "cmake",
        "ninja-build",
        "git",
        "build-essential",
        "pkg-config"
    ])

    # Clone SVT-AV1
    run(["git", "clone", "--depth=1", "https://github.com/AOMediaCodec/SVT-AV1.git"])

    # Build
    run([
        "bash", "-c",
        "cd SVT-AV1 && "
        "mkdir -p build && cd build && "
        "cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON .. && "
        "ninja"
    ])

    # Install
    run(["sudo", "bash", "-c", "cd SVT-AV1/build && ninja install"])

    # Ensure pkg-config can find it
    run(["sudo", "ldconfig"])

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
        "libdrm-dev"
    ])

    # Build SVT-AV1 from source
    build_svt_av1()

    config = json.loads(CONFIG_PATH.read_text())

    # AMD VAAPI
    for backend in config["amd"].values():
        if backend["enabled"]:
            install_packages(backend.get("packages", []))

    # Intel VAAPI
    for backend in config["intel"].values():
        if backend["enabled"]:
            install_packages(backend.get("packages", []))

if __name__ == "__main__":
    main()

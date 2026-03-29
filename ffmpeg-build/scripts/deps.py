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
    install_packages([
        "cmake",
        "ninja-build",
        "git",
        "build-essential",
        "pkg-config"
    ])

    run([
        "git", "clone",
        "--recurse-submodules",
        "https://gitlab.com/AOMediaCodec/SVT-AV1.git"
    ])

    run([
        "bash", "-c",
        "cd SVT-AV1 && "
        "mkdir -p build && cd build && "
        "cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=OFF \
            -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
            .. && \
         ninja"
    ])

    run(["sudo", "bash", "-c", "cd SVT-AV1/build && ninja install"])
    run(["sudo", "ldconfig"])


def install_ffnvcodec_headers():
    run(["git", "clone", "--depth=1", "https://github.com/FFmpeg/nv-codec-headers.git"])
    run(["bash", "-c", "cd nv-codec-headers && make && sudo make install"])


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

    install_ffnvcodec_headers()

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

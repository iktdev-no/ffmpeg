#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run([
        "sudo", "apt-get", "install", "-y",
        "git",
        "cmake",
        "ninja-build",
        "build-essential",
        "pkg-config",
        "nasm",
        "yasm"
    ])

    run(["git", "clone", "--recurse-submodules", "https://gitlab.com/AOMediaCodec/SVT-AV1.git"])

    run([
        "bash", "-c",
        "cd SVT-AV1 && "
        "mkdir -p build && cd build && "
        "cmake -G Ninja "
        "-DCMAKE_BUILD_TYPE=Release "
        "-DBUILD_SHARED_LIBS=OFF "
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON "
        ".. && "
        "ninja && sudo ninja install"
    ])

    run(["sudo", "ldconfig"])

if __name__ == "__main__":
    main()

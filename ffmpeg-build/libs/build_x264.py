#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y",
         "git", "build-essential", "nasm", "pkg-config"])

    run(["git", "clone", "--depth=1",
         "https://code.videolan.org/videolan/x264.git"])

    run(["bash", "-c",
         "cd x264 && "
         "./configure "
         "--enable-static "
         "--enable-pic "
         "--disable-opencl "
         "--disable-asm "
         "--disable-cli && "
         "make -j$(nproc) && "
         "sudo make install"])

    run(["sudo", "ldconfig"])

    # sanity check
    run(["bash", "-c", "pkg-config --static --libs x264"])

    run(["bash", "-c", r"""
    pkg-config --static --exists x264 || {
    echo "ERROR: x264 not visible via pkg-config"
    exit 1
    }
    pkg-config --static --libs x264
    """])

if __name__ == "__main__":
    main()
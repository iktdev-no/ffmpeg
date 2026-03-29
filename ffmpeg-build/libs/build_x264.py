#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "build-essential", "nasm"])

    run(["git", "clone", "--depth=1", "https://code.videolan.org/videolan/x264.git"])
    run(["bash", "-c",
         "cd x264 && "
         "./configure --enable-static --disable-opencl --disable-cli && "
         "make -j$(nproc) && sudo make install"])
    run(["sudo", "ldconfig"])

if __name__ == "__main__":
    main()

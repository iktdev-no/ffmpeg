#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "build-essential", "yasm"])

    run(["git", "clone", "--depth=1", "https://chromium.googlesource.com/webm/libvpx.git"])
    run(["bash", "-c",
         "cd libvpx && "
         "./configure --enable-vp8 --enable-vp9 --enable-static --disable-shared "
         "--disable-examples --disable-tools --disable-docs && "
         "make -j$(nproc) && sudo make install"])
    run(["sudo", "ldconfig"])

if __name__ == "__main__":
    main()

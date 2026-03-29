#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "build-essential"])

    run(["git", "clone", "--depth=1", "https://github.com/FFmpeg/nv-codec-headers.git"])
    run(["bash", "-c", "cd nv-codec-headers && make && sudo make install"])

if __name__ == "__main__":
    main()

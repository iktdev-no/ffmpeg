#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "cmake", "ninja-build", "build-essential"])

    run(["git", "clone", "--depth=1", "https://github.com/videolan/x265.git"])
    run(["bash", "-c",
         "cd x265/build/linux && "
         "cmake -G Ninja -DCMAKE_BUILD_TYPE=Release "
         "-DENABLE_SHARED=OFF -DENABLE_PIC=ON ../../source && "
         "ninja && sudo ninja install"])
    run(["sudo", "ldconfig"])

if __name__ == "__main__":
    main()

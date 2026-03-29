#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "git", "cmake", "ninja-build", "build-essential"])

    run(["git", "clone", "--depth=1", "https://aomedia.googlesource.com/aom"])
    run(["bash", "-c",
         "cd aom && mkdir -p build && cd build && "
         "cmake -G Ninja -DCMAKE_BUILD_TYPE=Release "
         "-DBUILD_SHARED_LIBS=OFF -DENABLE_TESTS=OFF -DENABLE_EXAMPLES=OFF .. && "
         "ninja && sudo ninja install"])
    run(["sudo", "ldconfig"])

if __name__ == "__main__":
    main()

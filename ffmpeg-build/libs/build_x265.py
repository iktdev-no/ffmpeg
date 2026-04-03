#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y",
         "git", "cmake", "ninja-build", "build-essential", "pkg-config"])

    run(["rm", "-rf", "x265"])
    run(["git", "clone", "--depth=1", "https://github.com/videolan/x265.git"])

    run(["bash", "-c",
         "mkdir -p x265/build && cd x265/build && "
         "cmake -G Ninja ../source "
         "-DCMAKE_BUILD_TYPE=Release "
         "-DENABLE_SHARED=OFF "
         "-DENABLE_PIC=ON "
         "-DCMAKE_INSTALL_PREFIX=/usr/local && "
         "ninja && sudo ninja install"])

    run(["sudo", "ldconfig"])

    run(["bash", "-c", r"""
    set -e

    if [ -f /usr/local/include/x265.h ] && [ -f /usr/local/lib/libx265.a ]; then
      echo "x265 OK (lib)"
      exit 0
    fi

    if [ -f /usr/local/include/x265.h ] && [ -f /usr/local/lib64/libx265.a ]; then
      echo "x265 OK (lib64)"
      exit 0
    fi

    echo "ERROR: x265 install incomplete"
    exit 1
    """])

if __name__ == "__main__":
    main()
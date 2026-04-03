#!/usr/bin/env python3
from utils import run

def main():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y",
         "git", "cmake", "ninja-build", "build-essential", "pkg-config"])

    run(["git", "clone", "--depth=1", "https://github.com/videolan/x265.git"])

    run(["bash", "-c",
         "cd x265/build/linux && "
         "cmake -G Ninja -DCMAKE_BUILD_TYPE=Release "
         "-DENABLE_SHARED=OFF -DENABLE_PIC=ON "
         "-DCMAKE_INSTALL_PREFIX=/usr/local "
         "../../source && "
         "ninja && sudo ninja install"])

    run(["sudo", "ldconfig"])

    run(["bash", "-c", r"""
    test -f /usr/local/lib/pkgconfig/x265.pc || {
    test -f /usr/local/lib64/pkgconfig/x265.pc || {
    echo "ERROR: x265.pc missing (CMake install failed)"
    exit 1
    }}
    """])

if __name__ == "__main__":
    main()
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

    # 🔥 VERIFY + FIX pkg-config
    run(["bash", "-c", r"""
        if [ ! -f /usr/local/lib/pkgconfig/x265.pc ]; then
            echo "x265.pc missing - generating manually"

            sudo mkdir -p /usr/local/lib/pkgconfig

            cat <<EOF | sudo tee /usr/local/lib/pkgconfig/x265.pc
prefix=/usr/local
exec_prefix=\${prefix}
libdir=\${exec_prefix}/lib
includedir=\${prefix}/include

Name: x265
Description: HEVC encoder
Version: 3.5
Libs: -L\${libdir} -lx265
Cflags: -I\${includedir}
EOF
        else
            echo "x265.pc OK"
        fi
    """])

if __name__ == "__main__":
    main()
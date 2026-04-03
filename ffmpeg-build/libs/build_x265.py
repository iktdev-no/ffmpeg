#!/usr/bin/env python3
from utils import run

def main():
    # ─────────────────────────────
    # Install deps
    # ─────────────────────────────
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y",
         "git", "cmake", "ninja-build", "build-essential", "pkg-config"])

    # ─────────────────────────────
    # Clone x265
    # ─────────────────────────────
    run(["rm", "-rf", "x265"])
    run(["git", "clone", "--depth=1", "https://github.com/videolan/x265.git"])

    # ─────────────────────────────
    # Build x265 (FIXED: correct cmake root)
    # ─────────────────────────────
    run(["bash", "-c",
        "set -e && "
        "mkdir -p x265/build && cd x265/build && "
        "cmake -G Ninja ../source "
        "-DCMAKE_BUILD_TYPE=Release "
        "-DENABLE_SHARED=OFF "
        "-DENABLE_PIC=ON "
        "-DCMAKE_INSTALL_PREFIX=/usr/local && "
        "ninja && sudo ninja install"])

    run(["sudo", "ldconfig"])

    # ─────────────────────────────
    # Verify install (STRICT)
    # ─────────────────────────────
    run(["bash", "-c", r"""
    set -e

    if [ -f /usr/local/include/x265.h ] && [ -f /usr/local/lib/libx265.a ]; then
      echo "x265 OK (lib)"
    elif [ -f /usr/local/include/x265.h ] && [ -f /usr/local/lib64/libx265.a ]; then
      echo "x265 OK (lib64)"
    else
      echo "ERROR: x265 install incomplete"
      exit 1
    fi
    """])

    # ─────────────────────────────
    # Ensure pkg-config (FIXED + ROBUST fallback)
    # ─────────────────────────────
    run(["bash", "-c", r"""
    set -e

    export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig

    if pkg-config --exists x265; then
      echo "x265.pc already OK"
      exit 0
    fi

    echo "Generating missing x265.pc fallback"

    sudo mkdir -p /usr/local/lib/pkgconfig

    LIBDIR=""
    for d in /usr/local/lib /usr/local/lib64 /usr/lib/x86_64-linux-gnu; do
      if ls $d/libx265.a >/dev/null 2>&1; then
        LIBDIR=$d
        break
      fi
    done

    if [ -z "$LIBDIR" ]; then
      echo "ERROR: libx265 not found anywhere"
      exit 1
    fi

    sudo tee /usr/local/lib/pkgconfig/x265.pc > /dev/null <<EOF
prefix=/usr/local
exec_prefix=\${prefix}
libdir=${LIBDIR}
includedir=\${prefix}/include

Name: x265
Description: H.265/HEVC encoder library
Version: 3.5
Libs: -L${LIBDIR} -lx265 -lm -lpthread
Cflags: -I\${includedir}
EOF

    echo "x265.pc created successfully"
    """])

if __name__ == "__main__":
    main()
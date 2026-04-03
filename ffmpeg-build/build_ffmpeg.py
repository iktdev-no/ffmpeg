#!/usr/bin/env python3
import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict

FLAGS_PATH = Path("ffmpeg-build/generated-flags.txt")
DIST_PATH = Path("ffmpeg-build/dist")


def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, env=env)


def main() -> None:
    DIST_PATH.mkdir(parents=True, exist_ok=True)

    env: Dict[str, str] = os.environ.copy()

    # ─────────────────────────────
    # pkg-config (stable CI config)
    # ─────────────────────────────
    env["PKG_CONFIG_PATH"] = ":".join([
        "/usr/local/lib/pkgconfig",
        "/usr/local/lib64/pkgconfig",
        "/usr/lib/pkgconfig",
        "/usr/share/pkgconfig"
    ])

    env["PKG_CONFIG_LIBDIR"] = ""

    # ─────────────────────────────
    # IMPORTANT: static build flags must NOT be removed
    # ─────────────────────────────
    env["CFLAGS"] = "-I/usr/local/include"
    env["LDFLAGS"] = "-L/usr/local/lib -lpthread -lm -ldl"

    # ─────────────────────────────
    # System deps
    # ─────────────────────────────
    run(["sudo", "apt-get", "update"])
    run([
        "sudo", "apt-get", "install", "-y",
        "git", "nasm", "yasm", "pkg-config", "build-essential"
    ])

    # ─────────────────────────────
    # FFmpeg source
    # ─────────────────────────────
    run(["rm", "-rf", "ffmpeg"])
    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"])

    # ─────────────────────────────
    # HARD DIAGNOSTICS
    # ─────────────────────────────
    run(["bash", "-c", "which pkg-config"], env=env)
    run(["bash", "-c", "pkg-config --version"], env=env)
    run(["bash", "-c", "echo $PKG_CONFIG_PATH"], env=env)
    run(["bash", "-c", "pkg-config --variable pc_path pkg-config"], env=env)

    run(["bash", "-c", "ls -R /usr/local/lib/pkgconfig || true"], env=env)
    run(["bash", "-c", "ls -R /usr/local/lib64/pkgconfig || true"], env=env)

    # STRICT validation
    run(["bash", "-c", "pkg-config --exists x264 || exit 1"], env=env)
    run(["bash", "-c", "pkg-config --exists x265 || exit 1"], env=env)

    # ─────────────────────────────
    # Load flags
    # ─────────────────────────────
    flags = FLAGS_PATH.read_text().replace("\n", " ").strip()

    # ─────────────────────────────
    # CONFIGURE (FIXED: env inline to avoid CI shell loss)
    # ─────────────────────────────
    configure_cmd = f"""
    set -e
    cd ffmpeg

    ./configure {flags} \
        --pkg-config=pkg-config \
        --pkg-config-flags="--static" \
        --prefix=/usr/local \
        --enable-static \
        --disable-shared \
        --extra-cflags='-I/usr/local/include' \
        --extra-ldflags='-L/usr/local/lib'
    """

    run(["bash", "-c", configure_cmd], env=env)

    # ─────────────────────────────
    # Build
    # ─────────────────────────────
    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"], env=env)

    # ─────────────────────────────
    # Output binaries
    # ─────────────────────────────
    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH / "ffmpeg")])
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH / "ffprobe")])

    print("\n✅ FFmpeg build complete (FIXED + static-safe)")


if __name__ == "__main__":
    main()
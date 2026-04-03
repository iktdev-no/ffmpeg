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
    # Force correct pkg-config scope
    # ─────────────────────────────
    env["PKG_CONFIG_PATH"] = (
        "/usr/local/lib/pkgconfig:"
        "/usr/lib/pkgconfig:"
        "/usr/share/pkgconfig"
    )

    env["CFLAGS"] = "-I/usr/local/include"
    env["LDFLAGS"] = "-L/usr/local/lib"

    run(["sudo", "apt-get", "update"], env=env)
    run(["sudo", "apt-get", "install", "-y",
         "git",
         "nasm",
         "yasm",
         "pkg-config"
    ], env=env)

    # Clean clone
    run(["rm", "-rf", "ffmpeg"], env=env)
    run(["git", "clone", "--depth=1", "https://github.com/ffmpeg/ffmpeg.git"], env=env)

    # ─────────────────────────────
    # Debug: verify libs BEFORE configure
    # ─────────────────────────────
    run(["bash", "-c", "pkg-config --exists x264 && echo x264 OK || echo x264 MISSING"], env=env)
    run(["bash", "-c", "pkg-config --exists x265 && echo x265 OK || echo x265 MISSING"], env=env)

    run(["bash", "-c", "ls -R /usr/local/lib/pkgconfig || true"], env=env)

    flags = FLAGS_PATH.read_text().replace("\n", " ").strip()

    # ─────────────────────────────
    # IMPORTANT: fully explicit static linking
    # ─────────────────────────────
    configure_cmd = f"""
    ./configure {flags} \
    --prefix=/usr/local \
    --enable-static \
    --disable-shared \
    --pkg-config-flags=--static \
    --extra-cflags='-I/usr/local/include' \
    --extra-ldflags='-L/usr/local/lib \
        -lx264 -lx265 -laom -lvpx -lSvtAv1Enc \
        -lpthread -lm -lz -ldl'
    """

    # ─────────────────────────────
    # Run configure with guaranteed env
    # ─────────────────────────────
    run([
        "bash",
        "-c",
        f"cd ffmpeg && PKG_CONFIG_PATH={env['PKG_CONFIG_PATH']} {configure_cmd}"
    ], env=env)

    # Build
    run(["bash", "-c", "cd ffmpeg && make -j$(nproc) V=1"], env=env)

    # Copy artifacts
    run(["cp", "ffmpeg/ffmpeg", str(DIST_PATH / "ffmpeg")], env=env)
    run(["cp", "ffmpeg/ffprobe", str(DIST_PATH / "ffprobe")], env=env)


if __name__ == "__main__":
    main()
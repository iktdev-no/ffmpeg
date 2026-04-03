#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# CONFIG SCHEMA
# ─────────────────────────────────────────────
class CodecConfig(BaseModel):
    enabled: bool = False
    packages: List[str] = Field(default_factory=list)
    ffmpegFlags: List[str] = Field(default_factory=list)


class CPUConfig(CodecConfig):
    pass


class GPUCodec(CodecConfig):
    description: Optional[str] = None


class GPUGroup(BaseModel):
    vaapi: Optional[GPUCodec] = None
    amf: Optional[GPUCodec] = None
    nvenc: Optional[GPUCodec] = None
    qsv: Optional[GPUCodec] = None


class Config(BaseModel):
    cpu: Optional[CPUConfig] = None
    amd: Optional[GPUGroup] = None
    nvidia: Optional[GPUGroup] = None
    intel: Optional[GPUGroup] = None


# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
CONFIG_FILE = "ffmpeg-build/config/gpu-backends.json"
WORKDIR = Path("build")
PREFIX = "/usr/local"


# ─────────────────────────────────────────────
# EXEC HELPERS
# ─────────────────────────────────────────────
def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    print("▶", " ".join(cmd))
    subprocess.check_call(cmd, env=env)


def sh(cmd: str, env: Optional[Dict[str, str]] = None) -> None:
    print("▶ bash:", cmd)
    subprocess.check_call(["bash", "-c", cmd], env=env)


# ─────────────────────────────────────────────
# LOAD CONFIG
# ─────────────────────────────────────────────
def load_config() -> Config:
    with open(CONFIG_FILE, "r") as f:
        raw = json.load(f)
    return Config.model_validate(raw)


# ─────────────────────────────────────────────
# INSTALL PACKAGES
# ─────────────────────────────────────────────
def install_packages(config: Config) -> None:
    pkgs = {
        "git",
        "nasm",
        "yasm",
        "pkg-config",
        "build-essential",
        "cmake",
        "ninja-build",
    }

    def add(codec: Optional[CodecConfig]):
        if codec:
            pkgs.update(codec.packages)

    add(config.cpu)

    for group in [config.amd, config.nvidia, config.intel]:
        if group:
            for codec in group.model_dump().values():
                if isinstance(codec, dict):
                    pkgs.update(codec.get("packages", []))

    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", *pkgs])


# ─────────────────────────────────────────────
# BUILD FLAGS
# ─────────────────────────────────────────────
def build_ffmpeg_flags(config: Config) -> str:
    flags: List[str] = []

    def add(codec: Optional[CodecConfig]):
        if codec and codec.enabled:
            flags.extend(codec.ffmpegFlags)

    add(config.cpu)

    for group in [config.amd, config.nvidia, config.intel]:
        if group:
            for codec in group.model_dump().values():
                if isinstance(codec, dict) and codec.get("enabled"):
                    flags.extend(codec.get("ffmpegFlags", []))

    flags += [
        f"--prefix={PREFIX}",
        "--enable-pic",
    ]

    return " ".join(flags)


# ─────────────────────────────────────────────
# BUILD CODECS
# ─────────────────────────────────────────────
def build_cpu_codecs(config: Config, env: Dict[str, str]) -> None:
    if not config.cpu or not config.cpu.enabled:
        return

    print("\n🔥 Building CPU codecs")

    # x264
    sh("""
        rm -rf x264 && \
        git clone --depth=1 https://code.videolan.org/videolan/x264.git && \
        cd x264 && \
        ./configure --prefix=/usr/local --enable-static --enable-pic && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    # x265
    sh("""
        rm -rf x265 && \
        git clone --depth=1 https://github.com/videolan/x265.git && \
        cd x265/build/linux && \
        cmake ../../source \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DENABLE_SHARED=OFF \
            -DENABLE_PIC=ON \
            -DENABLE_AVX512=OFF && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    # 🔥 FIXED pkg-config
    sh(r"""
echo "Fixing x265 pkg-config"

sudo mkdir -p /usr/local/lib/pkgconfig

if [ -f /usr/local/lib/libx265.a ]; then
    LIBDIR=/usr/local/lib
elif [ -f /usr/local/lib64/libx265.a ]; then
    LIBDIR=/usr/local/lib64
else
    echo "ERROR: libx265 not found"
    exit 1
fi

sudo tee /usr/local/lib/pkgconfig/x265.pc > /dev/null <<EOF
prefix=/usr/local
exec_prefix=\${prefix}
libdir=${LIBDIR}
includedir=\${prefix}/include

Name: x265
Description: H.265/HEVC encoder
Version: 3.5
Libs: -L${LIBDIR} -lx265 -lpthread -lm
Cflags: -I\${includedir}
EOF

echo "==== x265.pc ===="
cat /usr/local/lib/pkgconfig/x265.pc

echo "==== pkg-config test ===="
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig pkg-config --libs x265 || exit 1
""", env)

    # aom
    sh("""
        rm -rf aom && \
        git clone --depth=1 https://aomedia.googlesource.com/aom && \
        mkdir -p aom/build && cd aom/build && \
        cmake .. \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DBUILD_SHARED_LIBS=OFF \
            -DENABLE_TESTS=OFF && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    # svt-av1
    sh("""
        rm -rf SVT-AV1 && \
        git clone --depth=1 https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
        cd SVT-AV1/Build && \
        cmake .. \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DBUILD_SHARED_LIBS=OFF && \
        make -j$(nproc) && \
        sudo make install
    """, env)


# ─────────────────────────────────────────────
# BUILD FFMPEG
# ─────────────────────────────────────────────
def build_ffmpeg(flags: str, env: Dict[str, str]) -> None:
    print("\n🚀 Building FFmpeg")

    # 🔥 DEBUG FIRST
    sh("pkg-config --list-all | grep x265 || true", env)
    sh("pkg-config --cflags x265 || true", env)
    sh("pkg-config --libs x265 || true", env)

    sh(f"""
        rm -rf ffmpeg && \
        git clone --depth=1 https://github.com/ffmpeg/ffmpeg.git && \
        cd ffmpeg && \
        ./configure {flags} \
            --enable-gpl \
            --enable-nonfree \
            --enable-static \
            --disable-shared \
            --pkg-config=pkg-config \
            --pkg-config-flags="--static" \
            --extra-cflags='-I/usr/local/include' \
            --extra-ldflags='-L/usr/local/lib' && \
        make -j$(nproc) && \
        sudo make install
    """, env)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main() -> None:
    config = load_config()

    env: Dict[str, str] = dict(os.environ)
    env["PKG_CONFIG_PATH"] = "/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
    env["PKG_CONFIG_ALLOW_SYSTEM_LIBS"] = "1"
    env["PKG_CONFIG_ALLOW_SYSTEM_CFLAGS"] = "1"
    env.pop("PKG_CONFIG_LIBDIR", None)

    WORKDIR.mkdir(exist_ok=True)

    install_packages(config)
    build_cpu_codecs(config, env)

    flags = build_ffmpeg_flags(config)

    print("\n📦 FFmpeg flags:")
    print(flags)

    build_ffmpeg(flags, env)

    print("\n✅ DONE: FFmpeg build complete")


if __name__ == "__main__":
    main()
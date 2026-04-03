#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# CONFIG SCHEMA (PYDANTIC)
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
CONFIG_FILE = "ffmpeg-config.json"
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
# LOAD CONFIG (STRICT VALIDATION HERE)
# ─────────────────────────────────────────────
def load_config() -> Config:
    with open(CONFIG_FILE, "r") as f:
        raw = json.load(f)
    return Config.model_validate(raw)


# ─────────────────────────────────────────────
# INSTALL SYSTEM PACKAGES
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

    if config.cpu:
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
                if isinstance(codec, GPUCodec):
                    add(codec)

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

    sh("""
        rm -rf x264 && \
        git clone --depth=1 https://code.videolan.org/videolan/x264.git && \
        cd x264 && \
        ./configure --prefix=/usr/local --enable-static --enable-pic && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    sh("""
        rm -rf x265 && \
        git clone --depth=1 https://github.com/videolan/x265.git && \
        cd x265/build/linux && \
        cmake ../../source -G "Unix Makefiles" \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DENABLE_SHARED=OFF \
            -DENABLE_PIC=ON && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    sh("""
        rm -rf aom && \
        git clone --depth=1 https://aomedia.googlesource.com/aom && \
        mkdir -p aom/build && cd aom/build && \
        cmake .. -G "Unix Makefiles" \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DBUILD_SHARED_LIBS=OFF \
            -DENABLE_TESTS=OFF && \
        make -j$(nproc) && \
        sudo make install
    """, env)

    sh("""
        rm -rf SVT-AV1 && \
        git clone --depth=1 https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
        cd SVT-AV1/Build && \
        cmake .. -G "Unix Makefiles" \
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

    env = dict(os.environ)
    env["PKG_CONFIG_PATH"] = "/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig"
    env["PKG_CONFIG_LIBDIR"] = ""

    WORKDIR.mkdir(exist_ok=True)

    install_packages(config)
    build_cpu_codecs(config, env)

    flags = build_ffmpeg_flags(config)

    print("\n📦 FFmpeg flags:")
    print(flags)

    build_ffmpeg(flags, env)

    print("\n✅ DONE: Pydantic-driven FFmpeg build complete")


if __name__ == "__main__":
    main()
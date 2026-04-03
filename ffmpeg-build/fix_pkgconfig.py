from pathlib import Path

def write_x265_pc():
    pc_path = Path("/usr/local/lib/pkgconfig/x265.pc")
    pc_path.parent.mkdir(parents=True, exist_ok=True)

    content = """prefix=/usr/local
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include

Name: x265
Description: H.265/HEVC encoder library
Version: 0.0
Libs: -L${libdir} -lx265 -lm -lpthread
Cflags: -I${includedir}
"""

    pc_path.write_text(content)
    print("[FIX] Generated missing x265.pc")

def main():
    # ONLY fix missing critical pkg-config files
    if not Path("/usr/local/lib/pkgconfig/x265.pc").exists():
        write_x265_pc()

if __name__ == "__main__":
    main()
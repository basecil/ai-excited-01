"""Entry point for ai-excited-01: The Whale That Swallowed the Moon.

Writes one image to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png
for local runs). Standard library only: the renderer in generate.py draws
every pixel with math, random, struct and zlib.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    png = generate.render()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()

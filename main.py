"""Entrypoint: render the entry image to $MAKEFUN_OUTPUT_DIR/entry.png.

Output defaults to /output (the grader runs /bot read-only with
MAKEFUN_OUTPUT_DIR unset, so a repo-relative default would fail).
Pure standard library only.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    png = generate.render_png()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()

"""Entry point for the ai-excited-01 submission.

Writes exactly one image, entry.png, to the output directory.
The grader runs /bot read-only with MAKEFUN_OUTPUT_DIR unset, so the
default is /output (never a repo-relative path).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = generate.render_png()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()

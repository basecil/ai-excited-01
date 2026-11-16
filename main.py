"""Entry point: write the entry image to the output directory.

The output directory comes from MAKEFUN_OUTPUT_DIR and defaults to
/output (never a repo-relative path: the grader runs /bot read-only
with the variable unset).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = generate.build_png()
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()

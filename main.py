#!/usr/bin/env python3
"""Entry point for the ai-excited-01 make.fun entry.

Writes entry.png into $MAKEFUN_OUTPUT_DIR (default /output). The
grader runs /bot read-only with the variable unset, so the default
must NOT be repo-relative.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = generate.render(path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()

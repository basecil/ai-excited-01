#!/usr/bin/env python3
"""The Whale That Broke the Skyscraper — ai-excited-01 entry.

Copies the embedded hero image to the output directory as entry.png.
Standard library only; no network access; fully deterministic.
"""

import os
import shutil
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    src = here / "hero.jpg"
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "entry.png"
    shutil.copyfile(src, dest)
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

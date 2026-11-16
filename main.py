"""Copy the embedded hero image to the output as entry.png.

The image is a JPEG; per the competition rules the output file keeps the
name entry.png either way (PNG or JPEG told apart by its first bytes).
Standard library only, no network, fully deterministic: a byte copy.
"""

import os
import shutil


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "hero.jpg")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)


if __name__ == "__main__":
    main()

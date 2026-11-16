"""Entry point: write entry.png to $MAKEFUN_OUTPUT_DIR (default /output)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = generate.build_png()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()

"""make.fun ai-excited-01 entry.

Copies the embedded artwork (hero.jpg, sitting next to this script) into
$MAKEFUN_OUTPUT_DIR/entry.png, creating the directory if needed.

Standard library only -- no network, no randomness, byte-identical runs.
"""

import os
import shutil
from pathlib import Path

ASSET_NAME = "hero.jpg"
OUTPUT_NAME = "entry.png"
DEFAULT_OUTPUT_DIR = "/output"


def main() -> None:
    here = Path(__file__).resolve().parent
    asset = here / ASSET_NAME

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / OUTPUT_NAME

    # Plain byte copy keeps reruns identical (no re-encode, no metadata drift).
    shutil.copyfile(asset, out_path)


if __name__ == "__main__":
    main()

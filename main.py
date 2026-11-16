"""Write the competition entry image to the configured output directory."""

import os
import shutil
from pathlib import Path


def main() -> None:
    """Copy the bundled hero image to $MAKEFUN_OUTPUT_DIR/entry.png."""
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve beside this script so the command works from any directory.
    source = Path(__file__).resolve().with_name("hero.jpg")
    destination = output_dir / "entry.png"

    shutil.copyfile(source, destination)


if __name__ == "__main__":
    main()

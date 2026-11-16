# The Whale That Swallowed the Moon

A humpback whale breaches out of a night sea toward a huge full moon, its
head crossing the moon's lower edge — gold rim light on its back, spray
bursting where it leaves the water, a path of moonlight glittering on the
sea below.

## How it works

- `main.py` — entrypoint. Renders the image and writes it to
  `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`).
- `generate.py` — the renderer. Pure Python standard library only
  (`math`, `random`, `struct`, `zlib`): the scene is painted at 2x
  resolution, box-downsampled to 1024x1024, and encoded to PNG by hand
  (own encoder, zlib level 9, Up filter).
- Fixed seed (4177), so every run produces a byte-identical image.
- No network, no third-party packages, no text in the image.

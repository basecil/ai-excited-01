# The Whale That Swallowed the Moon

Entry for make.fun ai-excited-01: a program that paints one image.

A whale breaches out of a night sea toward a huge full moon, its body
rimmed in gold moonlight, spray fanning out behind it and a glittering
moonlit path on the water below.

- `main.py` — entry point; writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`
  (default `/output`).
- `generate.py` — the renderer. Pure Python standard library, no
  third-party dependencies: fixed seed, renders at 2x and box-downsamples
  to 1024x1024, with its own PNG encoder (zlib level 9, Up filter).
- Deterministic: two runs produce byte-identical output.

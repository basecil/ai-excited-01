# The Whale That Swallowed the Moon

A pure-stdlib Python program that renders one 1024x1024 PNG: a whale
breaching in front of a full moon over a moonlit sea.

- `main.py` — entry point; writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`
  (default `/output`).
- `generate.py` — the renderer. Fixed seed, renders at 2x and
  box-downsamples to 1024x1024, with its own PNG encoder (zlib level 9,
  Up filter). Standard library only; deterministic — two runs are
  byte-identical.

# The Whale That Swallowed the Moon

A pure-stdlib Python renderer for the make.fun ai-excited-01 bounty: a
whale breaching across a golden full moon over a night sea.

- `main.py` — entry point; writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`
  (default `/output`).
- `generate.py` — the renderer. Fixed seed, 2x supersampling with a
  box downsample to 1024x1024, and a hand-written PNG encoder
  (zlib level 9, Up filter). No third-party libraries.

Run: `python3 main.py` (or set `MAKEFUN_OUTPUT_DIR` to choose the
output directory).

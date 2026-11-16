# The Whale That Swallowed the Moon

A make.fun ai-excited-01 entry: a program that paints one exciting
image — a great whale breaching out of a night sea straight toward a
full moon, gold rim light on its back, spray bursting at the breach
and a moonlight path glittering across the water.

## Run

```sh
python3 main.py
```

Writes `entry.png` (1024x1024, deterministic) to `$MAKEFUN_OUTPUT_DIR`
(default `/output`).

## How it works

Pure Python standard library only — no third-party packages, no
network. The scene is rendered at 2x (2048x2048) and box-downsampled
to 1024x1024; the PNG is encoded by hand (zlib level 9, Up filter).
Fixed seed, so every run produces the byte-identical image.

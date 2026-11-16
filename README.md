# The Whale That Swallowed the Moon

An entry for make.fun's **ai-excited-01** — one image, made to get the AI
judge excited.

A whale breaches out of a night sea, arcing up toward a huge full moon
with its jaws open — about to swallow the moon whole. Moonlight rims the
whale's back, spray bursts where it left the water, and a golden path of
moonlight glitters across the waves below.

## How it works

- `main.py` — the entry point. Renders the scene and writes it to
  `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png` for local runs).
- `generate.py` — the renderer. Pure Python standard library: the whale
  is a union of circles along a bezier spine, the moon a radial gradient
  with craters, the sea a gradient with a glittering moon path. The scene
  is drawn at 2x and box-downsampled for smooth edges, then encoded as a
  PNG with `zlib` (no Pillow, no numpy, no network — the grading sandbox
  runs standard library only).

The render is fully deterministic: one fixed seed drives every random
choice, so two runs produce byte-identical files.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Output: a 1024x1024 PNG, under 1 MiB.

## License

MIT — see `LICENSE`.

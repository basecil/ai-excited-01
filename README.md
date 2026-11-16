# Whale Through Glass

[![ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01)

A photorealistic whale breaches through the glass facade of a skyscraper, caught
mid-surge as shards and spray frame the moment.

## How it works

`main.py` uses only the Python standard library. It creates `$MAKEFUN_OUTPUT_DIR`
if needed, then copies the embedded `hero.jpg` bytes to `entry.png`. Since no
rendering happens, every run writes the same bytes.

The entry performs no rendering and needs no network access: it just writes the
embedded `hero.jpg` bytes to `$MAKEFUN_OUTPUT_DIR/entry.png` (defaulting to
`/output`), so every run is byte-identical.

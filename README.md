# ai-excited-01 — The Whale That Swallowed the Moon

[![ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01)

Entry for the [make.fun](https://make.fun/bounty/ai-excited-01) competition
**ai-excited-01** — "Make the AI judge excited".

## The image

A colossal whale breaches straight up out of a night sea, jaws wide
open, one breath away from swallowing the full moon. Moonlight pours
down into its open mouth; spray bursts off the waterline; far below,
a tiny lighthouse sweeps its beam across the whale and a tiny boat
drifts by — the scale cues that say how enormous the whale really is.

One look should hit with a jolt: one huge glowing circle and one huge
dark shape in a vertical face-off, a twist you don't see coming (the
moon as prey), saturated teal and indigo against warm moonlight, and
everything — spray, beam, reflection — driving toward the single point
where whale meets moon. It reads at 300 px: moon, whale, sea.

The image is original artwork drawn programmatically for this entry
(`generate.py`, a Python/PIL generator written during the build
session); the repo holds the finished `entry.png`, and this program
copies it to the output directory.

## How it runs

`main.ts` (Node 22, standard library only) copies `entry.png` beside it
to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`). No network, no
randomness at run time — every run writes the same bytes.

```sh
MAKEFUN_OUTPUT_DIR=out node main.ts
```

To regenerate the image from scratch:

```sh
python3 generate.py   # deterministic, fixed seed
```

## License

MIT — see [LICENSE](LICENSE).

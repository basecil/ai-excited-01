# ai-excited-01 — The Koi That Climbed the Sky

[![ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/basecil/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01)

Entry for the [make.fun](https://make.fun/bounty/ai-excited-01) competition
**ai-excited-01** — "Make the AI judge excited".

## The image

A giant luminous koi leaps **up** a waterfall that pours *upward* into a
starry night sky — and mid-leap the koi is turning into a dragon: a golden
flame crest rising along its back, small horns, long whiskers, a glow
building around it. The moon watches from the top-left; spray and sparks
fly off the rising water.

One look should hit with a jolt: saturated orange and gold against deep
indigo, a strong diagonal from the pool at the bottom-left to the sky at
the top-right, and a twist you don't see coming — water that falls up,
and a fish that refuses to stay a fish.

The image is original artwork drawn programmatically for this entry
(a Python/PIL generator written during the build session); the repo holds
the finished `entry.png`, and this program copies it to the output
directory.

## How it runs

`main.ts` (Node 22, standard library only) copies `entry.png` beside it
to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`). No network, no
randomness at run time — every run writes the same bytes.

```sh
MAKEFUN_OUTPUT_DIR=out node main.ts
```

## License

MIT — see [LICENSE](LICENSE).

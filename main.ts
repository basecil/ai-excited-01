// ai-excited-01 entry program ("The Whale That Swallowed the Moon").
//
// The repository holds the finished image as entry.png; this program
// places it at $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
// Node 22, standard library only, no network, no randomness —
// a plain file copy, so two runs always write identical bytes.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const here = dirname(fileURLToPath(import.meta.url));

mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));

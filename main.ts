import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Entry program for make.fun ai-excited-01: copies the image this
// repository holds to the output directory the harness requests.
// Deterministic by construction: a plain file copy, no network,
// no randomness — every run writes the same bytes.
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const here = dirname(fileURLToPath(import.meta.url));

mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));

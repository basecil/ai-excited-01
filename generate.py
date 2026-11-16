#!/usr/bin/env python3
"""The Whale That Swallowed the Moon — pure-stdlib renderer.

Paints one deterministic 1024x1024 PNG: a whale breaching toward a full
moon, gold rim light, a spray burst, and a moonlight path on the sea.
Standard library only (the grader installs nothing). Fixed seed, so
every run produces byte-identical output.
"""

import math
import random
import struct
import zlib

SEED = 4177
W, H = 1024, 1024
S = 2  # supersample factor; canvas is 2048x2048, box-downsampled
CW, CH = W * S, H * S
HORIZON = 640  # final px; sky above, sea below

SKY_TOP = (0x02, 0x06, 0x17)
SKY_HOR = (0x0B, 0x1E, 0x3A)
SEA_TOP = (0x0D, 0x1B, 0x33)
SEA_BOT = (0x04, 0x07, 0x0F)
MOON_CORE = (0xFF, 0xFB, 0xE8)
MOON_EDGE = (0xEE, 0xD6, 0x88)
GOLD = (0xF2, 0xC9, 0x6B)
PALE_GOLD = (0xFF, 0xE9, 0xB0)
BODY = (0x1C, 0x35, 0x50)
BODY_DARK = (0x14, 0x28, 0x3E)
BELLY = (0x42, 0x60, 0x7E)
WHITE = (0xF4, 0xF8, 0xFF)
DARK = (0x0A, 0x14, 0x20)

MOON_X, MOON_Y, MOON_R = 660, 270, 165


def lerp(a, b, t):
    return (int(round(a[0] + (b[0] - a[0]) * t)),
            int(round(a[1] + (b[1] - a[1]) * t)),
            int(round(a[2] + (b[2] - a[2]) * t)))


def blend(fg, bg, alpha):
    return (int(round(fg[0] * alpha + bg[0] * (1.0 - alpha))),
            int(round(fg[1] * alpha + bg[1] * (1.0 - alpha))),
            int(round(fg[2] * alpha + bg[2] * (1.0 - alpha))))


def sea_color(y):
    t = min(1.0, max(0.0, (y - HORIZON) / (H - HORIZON)))
    return lerp(SEA_TOP, SEA_BOT, t)


class Canvas:
    """RGB canvas as one flat bytearray; span fills are slice assigns."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def row(self, y, x0, x1, color):
        if y < 0 or y >= self.h:
            return
        if x0 < 0:
            x0 = 0
        if x1 > self.w:
            x1 = self.w
        if x0 >= x1:
            return
        i = (y * self.w + x0) * 3
        self.px[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1):
            self.row(y, x0, x1, color)

    def circle(self, cx, cy, r, color):
        if r <= 0:
            return
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = math.isqrt(r2 - dy * dy)
            self.row(y, cx - dx, cx + dx + 1, color)

    def polygon(self, pts, color):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.row(y, int(math.ceil(xs[j])), int(xs[j + 1]) + 1, color)


def bez(t):
    """Whale spine: quadratic bezier, tail -> control -> head (final px)."""
    u = 1.0 - t
    return (u * u * 360.0 + 2 * u * t * 330.0 + t * t * 628.0,
            u * u * 720.0 + 2 * u * t * 480.0 + t * t * 352.0)


def bez_tangent(t):
    dx = 2 * (1 - t) * (330.0 - 360.0) + 2 * t * (628.0 - 330.0)
    dy = 2 * (1 - t) * (480.0 - 720.0) + 2 * t * (352.0 - 480.0)
    n = math.hypot(dx, dy)
    return (dx / n, dy / n)


def body_radius(t):
    """Radius profile 18 -> 95 -> 44 along the spine (final px)."""
    if t < 0.55:
        s = t / 0.55
        s = s * s * (3 - 2 * s)
        return 18 + 77 * s
    s = (t - 0.55) / 0.45
    s = s * s * (3 - 2 * s)
    return 95 - 51 * s


def down_normal(t):
    """Unit normal to the spine pointing downward (toward the water)."""
    tx, ty = bez_tangent(t)
    nx, ny = -ty, tx
    if ny < 0:
        nx, ny = -nx, -ny
    return (nx, ny)


def render():
    rng = random.Random(SEED)
    cv = Canvas(CW, CH)

    # --- sky gradient ---
    for y in range(HORIZON * S):
        cv.row(y, 0, CW, lerp(SKY_TOP, SKY_HOR, y / (HORIZON * S)))
    # --- sea gradient ---
    for y in range(HORIZON * S, CH):
        cv.row(y, 0, CW, lerp(SEA_TOP, SEA_BOT,
                              (y - HORIZON * S) / ((H - HORIZON) * S)))

    # --- 280 stars, clear zone around the moon ---
    placed = 0
    while placed < 280:
        x = rng.uniform(0, W)
        y = rng.uniform(0, HORIZON - 10)
        if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 220.0 ** 2:
            continue
        s = rng.random()
        r = 1 if s < 0.7 else (2 if s < 0.95 else 3)
        bright = rng.uniform(0.55, 1.0)
        base = blend(WHITE, (0xCF, 0xDC, 0xFF), rng.random())
        col = tuple(max(0, min(255, int(c * bright))) for c in base)
        cv.circle(int(x * S), int(y * S), max(1, (r * S) // 2), col)
        placed += 1

    # --- moon glow halo: 36 rings, largest first ---
    sky_mid = lerp(SKY_TOP, SKY_HOR, MOON_Y / HORIZON)
    for i in range(36):
        t = i / 35.0
        rad = (380 - 210 * t) * S
        col = blend(GOLD, sky_mid, 0.04 + 0.41 * t)
        cv.circle(MOON_X * S, MOON_Y * S, int(rad), col)

    # --- moon disc gradient: 24 rings, edge to core ---
    for i in range(24):
        t = i / 23.0
        rad = (165 - 157 * t) * S
        cv.circle(MOON_X * S, MOON_Y * S, int(rad),
                  lerp(MOON_EDGE, MOON_CORE, t))

    # --- 16 craters ---
    for _ in range(16):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 135)
        cx = MOON_X + d * math.cos(a)
        cy = MOON_Y + d * math.sin(a)
        cr = rng.uniform(6, 18)
        col = lerp(MOON_EDGE, (0xC9, 0xAE, 0x6E), rng.uniform(0.3, 0.8))
        cv.circle(int(cx * S), int(cy * S), int(cr * S), col)

    # --- moonlight path: 8 gold strips, widening with depth ---
    for i in range(8):
        y = 655 + i * 45 + rng.uniform(-6, 6)
        half = 35 + i * 22
        cx = MOON_X + rng.uniform(-12, 12)
        hh = rng.uniform(4, 9)
        col = blend(GOLD, sea_color(y), 0.45 + 0.35 * rng.random())
        cv.rect(int((cx - half) * S), int(y * S),
                int((cx + half) * S), int((y + hh) * S), col)

    # --- 420 sparkle dashes on the path ---
    for _ in range(420):
        y = rng.uniform(648, 1015)
        depth = (y - HORIZON) / (H - HORIZON)
        half = 30 + depth * 190
        x = MOON_X + rng.uniform(-half, half)
        w = rng.uniform(4, 14)
        hh = rng.uniform(1.5, 3)
        col = blend(PALE_GOLD, sea_color(y), rng.uniform(0.35, 0.9))
        cv.rect(int(x * S), int(y * S),
                int((x + w) * S), int((y + hh) * S), col)

    # --- whale: union of 29 circles along the spine ---
    spine = [(bez(i / 28.0), body_radius(i / 28.0)) for i in range(29)]
    # gold rim light (same body shifted +17,-13), drawn first
    for (x, y), r in spine:
        cv.circle(int((x + 17) * S), int((y - 13) * S), int(r * S), GOLD)
    # body
    for (x, y), r in spine:
        cv.circle(int(x * S), int(y * S), int(r * S), BODY)

    # --- belly: lighter circles inside the body, lower edge ---
    for k in range(6):
        t = 0.32 + k * 0.07
        (x, y), r = bez(t), body_radius(t)
        nx, ny = down_normal(t)
        bx = x + nx * 0.42 * r
        by = y + ny * 0.42 * r
        cv.circle(int(bx * S), int(by * S), int(0.42 * r * S), BELLY)

    # --- flukes: rounded lobes at the tail, gold top rim ---
    # (x, y, r) in final px; lobes overlap the tail and each other
    lobes = [(315, 700, 24), (338, 710, 17), (360, 712, 15),
             (382, 710, 17), (405, 697, 24)]
    for (x, y, r) in lobes:
        cv.circle(int(x * S), int((y - 4) * S), int(r * S), GOLD)
    for (x, y, r) in lobes:
        cv.circle(int(x * S), int(y * S), int(r * S), BODY)

    # --- pectoral fin: tapered polygon ---
    fin = [(395, 515), (425, 550), (390, 585), (345, 608)]
    cv.polygon([(x * S, y * S) for (x, y) in fin], BODY_DARK)

    # --- eye: pale dot + dark pupil at the head ---
    cv.circle(645 * S, 338 * S, 6 * S, (0xE8, 0xF0, 0xF8))
    cv.circle(645 * S, 338 * S, 3 * S, DARK)

    # --- 30 foam blobs at the waterline ---
    for _ in range(30):
        x = rng.uniform(295, 435)
        y = rng.uniform(632, 652)
        fr = rng.uniform(3, 8)
        col = blend(WHITE, sea_color(y), rng.uniform(0.0, 0.35))
        cv.circle(int(x * S), int(y * S), int(fr * S), col)

    # --- spray: 320 droplets in an upward fan at the breach ---
    bx, by = 360.0, 640.0
    for _ in range(320):
        a = rng.uniform(-2.8, -0.35)
        dist = rng.uniform(5, 130) * (0.4 + 0.6 * rng.random())
        x = bx + dist * math.cos(a)
        y = by + dist * math.sin(a)
        size = max(0.8, rng.uniform(1, 3.5) * (1.0 - dist / 220.0))
        bright = rng.uniform(0.7, 1.0)
        col = tuple(int(c * bright)
                    for c in blend(WHITE, PALE_GOLD, rng.random() * 0.5))
        cv.circle(int(x * S), int(y * S), max(1, int(size * S)), col)

    # --- 70 sheeting droplets on the trailing edge ---
    for _ in range(70):
        t = rng.uniform(0.05, 0.5)
        (x, y), r = bez(t), body_radius(t)
        nx, ny = down_normal(t)
        off = r * rng.uniform(0.9, 1.35)
        dx = x + nx * off + rng.uniform(-6, 6)
        dy = y + ny * off + rng.uniform(-6, 6)
        size = rng.uniform(1, 3)
        cv.circle(int(dx * S), int(dy * S), max(1, int(size * S)), WHITE)

    return cv


def downsample(cv):
    """Box-downsample the 2x canvas to the final size."""
    out = bytearray(W * H * 3)
    stride = CW * 3
    px = cv.px
    for oy in range(H):
        r0 = 2 * oy * stride
        r1 = r0 + stride
        o = oy * W * 3
        for ox in range(W):
            i0 = r0 + ox * 6
            i1 = r1 + ox * 6
            out[o] = (px[i0] + px[i0 + 3] + px[i1] + px[i1 + 3] + 2) >> 2
            out[o + 1] = (px[i0 + 1] + px[i0 + 4] +
                          px[i1 + 1] + px[i1 + 4] + 2) >> 2
            out[o + 2] = (px[i0 + 2] + px[i0 + 5] +
                          px[i1 + 2] + px[i1 + 5] + 2) >> 2
            o += 3
    return out


def _chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def encode_png(rgb, w, h):
    """PNG encoder: Up filter, zlib level 9."""
    stride = w * 3
    raw = bytearray()
    prev = bytes(stride)
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        filt = bytearray(stride)
        for i in range(stride):
            filt[i] = (row[i] - prev[i]) & 0xFF
        raw.append(2)  # filter type 2 = Up (subtract the row above)
        raw += filt
        prev = row
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def build():
    return encode_png(downsample(render()), W, H)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    data = build()
    with open(out, "wb") as f:
        f.write(data)
    print(f"wrote {out} ({len(data)} bytes)")

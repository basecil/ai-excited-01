#!/usr/bin/env python3
"""The Whale That Swallowed the Moon -- pure-stdlib renderer.

A 1024x1024 flat illustration: a whale breaching across a golden full
moon over a night sea. Rendered at 2x and box-downsampled for smooth
edges. Standard library only (math, random, struct, sys, zlib) because
the grader runs with no third-party packages installed.

Layout (final 1024x1024 coordinates):
  * sky gradient #020617 -> #0b1e3a, horizon at y=640
  * sea gradient #0d1b33 -> #04070f
  * moon centre (660, 270), radius 165, warm core to golden edge,
    36-ring glow halo, 16 craters, 280 stars with a clear zone
  * moonlight path: 8 gold strips + 420 sparkle dashes, widening
    with depth
  * whale: 29 circles along a quadratic bezier spine from tail
    (360, 720) through control (330, 480) to head (628, 352),
    radius profile 18 -> 95 -> 44; gold rim light shifted (+17, -13);
    lighter belly clipped to the body; flukes and pectoral fin;
    pale eye with dark pupil; spray fan + sheeting droplets + foam
  * PNG written by a hand-rolled encoder: zlib level 9, Up filter

Deterministic: one fixed seed (4177) drives every random choice, so
two runs produce byte-identical output.
"""

import math
import random
import struct
import sys
import zlib

SEED = 4177
W = 1024
H = 1024
SS = 2  # supersample factor
W2 = W * SS
H2 = H * SS

SKY_TOP = (2, 6, 23)       # #020617
SKY_HORIZON = (11, 30, 58)  # #0b1e3a
SEA_TOP = (13, 27, 51)     # #0d1b33
SEA_BOTTOM = (4, 7, 15)    # #04070f
HORIZON = 640

MOON_C = (660, 270)
MOON_R = 165
MOON_CORE = (255, 251, 232)  # #fffbe8
MOON_EDGE = (238, 214, 136)  # #eed688
HALO_COLOR = (247, 215, 116)
HALO_RINGS = 36
HALO_STEP = 6  # final px per ring

BODY = (38, 74, 106)
BODY_DARK = (29, 58, 86)
BELLY = (111, 151, 196)
RIM = (255, 207, 110)
GOLD_PATH = (242, 201, 107)
FOAM = (214, 233, 247)

TAIL = (360, 720)
CTRL = (330, 480)
HEAD = (628, 352)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def blend(fg, bg, alpha):
    return tuple(int(round(fg[i] * alpha + bg[i] * (1.0 - alpha)))
                 for i in range(3))


def sky_color(y):
    t = max(0.0, min(1.0, y / HORIZON))
    return lerp(SKY_TOP, SKY_HORIZON, t)


def sea_color(y):
    t = max(0.0, min(1.0, (y - HORIZON) / (H - HORIZON)))
    return lerp(SEA_TOP, SEA_BOTTOM, t)


def base_color(y):
    """Sky/sea gradient colour at final-py (float ok)."""
    return sky_color(y) if y < HORIZON else sea_color(y)


class Canvas:
    """2x framebuffer (list of bytearray rows, RGB) plus a body mask."""

    def __init__(self):
        self.rows = []
        for y2 in range(H2):
            c = base_color(y2 / SS)
            self.rows.append(bytearray(bytes(c) * W2))
        self.mask = [bytearray(W2) for _ in range(H2)]

    def span(self, y2, x0, x1, color):
        if y2 < 0 or y2 >= H2:
            return
        x0 = max(0, int(x0))
        x1 = min(W2, int(x1))
        if x1 <= x0:
            return
        row = self.rows[y2]
        row[x0 * 3:x1 * 3] = bytes(color) * (x1 - x0)

    def circle(self, cx, cy, r, color):
        """Solid filled circle; cx, cy, r in 2x coords."""
        cb = bytes(color)
        r2 = r * r
        y0 = max(0, int(math.ceil(cy - r)))
        y1 = min(H2, int(math.floor(cy + r)) + 1)
        for y2 in range(y0, y1):
            dy = y2 + 0.5 - cy
            d = r2 - dy * dy
            if d <= 0:
                continue
            dx = math.sqrt(d)
            x0 = max(0, int(math.ceil(cx - dx)))
            x1 = min(W2, int(math.floor(cx + dx)) + 1)
            if x1 > x0:
                row = self.rows[y2]
                row[x0 * 3:x1 * 3] = cb * (x1 - x0)

    def circle_mask(self, cx, cy, r):
        """Paint a filled circle into the body mask (value 1)."""
        r2 = r * r
        y0 = max(0, int(math.ceil(cy - r)))
        y1 = min(H2, int(math.floor(cy + r)) + 1)
        for y2 in range(y0, y1):
            dy = y2 + 0.5 - cy
            d = r2 - dy * dy
            if d <= 0:
                continue
            dx = math.sqrt(d)
            x0 = max(0, int(math.ceil(cx - dx)))
            x1 = min(W2, int(math.floor(cx + dx)) + 1)
            if x1 > x0:
                self.mask[y2][x0:x1] = b"\x01" * (x1 - x0)

    def circle_blend(self, cx, cy, r, color, alpha):
        """Filled circle alpha-blended over whatever is underneath."""
        r2 = r * r
        y0 = max(0, int(math.ceil(cy - r)))
        y1 = min(H2, int(math.floor(cy + r)) + 1)
        inv = 1.0 - alpha
        c0, c1, c2 = color
        for y2 in range(y0, y1):
            dy = y2 + 0.5 - cy
            d = r2 - dy * dy
            if d <= 0:
                continue
            dx = math.sqrt(d)
            x0 = max(0, int(math.ceil(cx - dx)))
            x1 = min(W2, int(math.floor(cx + dx)) + 1)
            row = self.rows[y2]
            for x in range(x0, x1):
                i = x * 3
                row[i] = int(c0 * alpha + row[i] * inv)
                row[i + 1] = int(c1 * alpha + row[i + 1] * inv)
                row[i + 2] = int(c2 * alpha + row[i + 2] * inv)

    def polygon(self, pts, color):
        """Solid scanline fill; pts are (x, y) in 2x coords."""
        cb = bytes(color)
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(H2, int(math.floor(max(ys))) + 1)
        n = len(pts)
        for y2 in range(y0, y1):
            yc = y2 + 0.5
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= yc < y2p) or (y2p <= yc < y1p):
                    t = (yc - y1p) / (y2p - y1p)
                    xs.append(x1 + t * (x2 - x1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                x0 = max(0, int(math.ceil(xs[k])))
                x1 = min(W2, int(math.floor(xs[k + 1])) + 1)
                if x1 > x0:
                    row = self.rows[y2]
                    row[x0 * 3:x1 * 3] = cb * (x1 - x0)


def draw_stars(cv, rng):
    clear = MOON_R + 55
    placed = 0
    tries = 0
    while placed < 280 and tries < 5000:
        tries += 1
        x = rng.uniform(0, W)
        y = rng.uniform(0, HORIZON - 8)
        dx = x - MOON_C[0]
        dy = y - MOON_C[1]
        if dx * dx + dy * dy < clear * clear:
            continue
        bright = rng.random()
        if bright > 0.92:
            r = rng.uniform(2.2, 3.0)
            col = (255, 255, 255)
        elif bright > 0.6:
            r = rng.uniform(1.4, 2.1)
            col = (232, 240, 255)
        else:
            r = rng.uniform(0.9, 1.5)
            col = (188, 211, 255)
        cv.circle(x * SS, y * SS, r * SS, col)
        placed += 1


def draw_halo(cv):
    cx, cy = MOON_C[0] * SS, MOON_C[1] * SS
    for i in range(HALO_RINGS):
        r_in = (MOON_R + i * HALO_STEP) * SS
        r_out = (MOON_R + (i + 1) * HALO_STEP) * SS
        alpha = 0.20 * (1.0 - i / HALO_RINGS) ** 1.6
        if alpha < 0.004:
            continue
        y0 = max(0, int(cy - r_out))
        y1 = min(H2, int(cy + r_out) + 1)
        for y2 in range(y0, y1):
            dy = y2 + 0.5 - cy
            d_out = r_out * r_out - dy * dy
            if d_out <= 0:
                continue
            dx_out = math.sqrt(d_out)
            d_in = r_in * r_in - dy * dy
            dx_in = math.sqrt(d_in) if d_in > 0 else 0.0
            # Sky/sea is uniform across a row, so the blend is a solid
            # per-row colour: no per-pixel work needed.
            col = bytes(blend(HALO_COLOR, base_color(y2 / SS), alpha))
            row = cv.rows[y2]
            lx0 = max(0, int(math.ceil(cx - dx_out)))
            lx1 = min(W2, int(math.floor(cx - dx_in)) + 1)
            if lx1 > lx0:
                row[lx0 * 3:lx1 * 3] = col * (lx1 - lx0)
            rx0 = max(0, int(math.ceil(cx + dx_in)))
            rx1 = min(W2, int(math.floor(cx + dx_out)) + 1)
            if rx1 > rx0:
                row[rx0 * 3:rx1 * 3] = col * (rx1 - rx0)


def draw_moon(cv):
    cx, cy, r = MOON_C[0] * SS, MOON_C[1] * SS, MOON_R * SS
    lut = [bytes(lerp(MOON_CORE, MOON_EDGE, (d / r) ** 0.9))
           for d in range(r + 1)]
    y0 = max(0, int(cy - r))
    y1 = min(H2, int(cy + r) + 1)
    for y2 in range(y0, y1):
        dy = y2 + 0.5 - cy
        d2y = dy * dy
        if d2y > r * r:
            continue
        dx = math.sqrt(r * r - d2y)
        x0 = max(0, int(math.ceil(cx - dx)))
        x1 = min(W2, int(math.floor(cx + dx)) + 1)
        row = cv.rows[y2]
        for x in range(x0, x1):
            ddx = x + 0.5 - cx
            d = int(math.sqrt(ddx * ddx + d2y))
            if d > r:
                continue
            row[x * 3:x * 3 + 3] = lut[d]


def draw_craters(cv, rng):
    for _ in range(16):
        ang = rng.uniform(0, 2 * math.pi)
        dist = math.sqrt(rng.random()) * (MOON_R - 26)
        x = MOON_C[0] + math.cos(ang) * dist
        y = MOON_C[1] + math.sin(ang) * dist
        cr = rng.uniform(6, 22)
        cv.circle_blend(x * SS, y * SS, cr * SS, (227, 209, 152), 0.45)


def draw_path(cv, rng):
    # 8 gold strips, widening with depth.
    for i in range(8):
        y = HORIZON + 18 + i * 44
        w = 60 + i * 30
        h = 7 + (i % 3)
        alpha = 0.16 - i * 0.008
        x0 = int((660 - w / 2) * SS)
        x1 = int((660 + w / 2) * SS)
        for y2 in range(int(y * SS), int((y + h) * SS)):
            if y2 >= H2:
                break
            col = bytes(blend(GOLD_PATH, sea_color(y2 / SS), alpha))
            cv.rows[y2][x0 * 3:x1 * 3] = col * (x1 - x0)
    # 420 sparkle dashes, spread widening with depth.
    for _ in range(420):
        y = rng.uniform(HORIZON + 6, H - 6)
        depth = (y - HORIZON) / (H - HORIZON)
        spread = 45 + depth * 230
        x = 660 + rng.gauss(0, spread / 2.2)
        w = rng.uniform(6, 14) + depth * 16
        h = rng.uniform(2, 3.5)
        alpha = rng.uniform(0.15, 0.5)
        y0 = int(y * SS)
        y1 = min(H2, int((y + h) * SS))
        x0 = max(0, int((x - w / 2) * SS))
        x1 = min(W2, int((x + w / 2) * SS))
        if x1 <= x0:
            continue
        for y2 in range(y0, y1):
            col = bytes(blend(GOLD_PATH, sea_color(y2 / SS), alpha))
            cv.rows[y2][x0 * 3:x1 * 3] = col * (x1 - x0)


def bezier(t):
    u = 1 - t
    x = u * u * TAIL[0] + 2 * u * t * CTRL[0] + t * t * HEAD[0]
    y = u * u * TAIL[1] + 2 * u * t * CTRL[1] + t * t * HEAD[1]
    return (x, y)


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def body_radius(t):
    if t < 0.55:
        return 18 + 77 * smooth(t / 0.55)
    return 95 - 51 * smooth((t - 0.55) / 0.45)


def draw_whale(cv):
    pts = []
    for i in range(29):
        t = i / 28
        pts.append((bezier(t), body_radius(t)))
    # Gold rim light: same body shape shifted (+17, -13), drawn first.
    for (x, y), r in pts:
        cv.circle((x + 17) * SS, (y - 13) * SS, r * SS, RIM)
    # Body, and the mask the belly is clipped to.
    for (x, y), r in pts:
        cv.circle(x * SS, y * SS, r * SS, BODY)
        cv.circle_mask(x * SS, y * SS, r * SS)
    # Flukes: concave polygon at the tail, gold underlay shifted up
    # so a gold rim shows along the top edge.
    fluke = [(345, 705), (255, 790), (320, 760), (360, 728),
             (400, 760), (465, 790), (375, 705)]
    cv.polygon([(x * SS, (y - 6) * SS) for x, y in fluke], RIM)
    cv.polygon([(x * SS, y * SS) for x, y in fluke], BODY)
    # Pectoral fin: tapered polygon, gold rim on the upper-right edge.
    fin = [(410, 495), (330, 585), (352, 600), (440, 530)]
    cv.polygon([((x + 6) * SS, (y - 6) * SS) for x, y in fin], RIM)
    cv.polygon([(x * SS, y * SS) for x, y in fin], BODY_DARK)


def draw_belly(cv):
    cb = bytes(BELLY)
    for i in range(24):
        t = 0.25 + (0.95 - 0.25) * i / 23
        (x, y), r = bezier(t), body_radius(t)
        cx, cy, cr = x * SS, (y + 0.38 * r) * SS, 0.72 * r * SS
        y0 = max(0, int(math.ceil(cy - cr)))
        y1 = min(H2, int(math.floor(cy + cr)) + 1)
        for y2 in range(y0, y1):
            dy = y2 + 0.5 - cy
            d = cr * cr - dy * dy
            if d <= 0:
                continue
            dx = math.sqrt(d)
            x0 = max(0, int(math.ceil(cx - dx)))
            x1 = min(W2, int(math.floor(cx + dx)) + 1)
            mask_row = cv.mask[y2]
            row = cv.rows[y2]
            x = x0
            while x < x1:
                if mask_row[x]:
                    xs = x
                    while x < x1 and mask_row[x]:
                        x += 1
                    row[xs * 3:x * 3] = cb * (x - xs)
                else:
                    x += 1


def draw_eye(cv):
    cv.circle(648 * SS, 332 * SS, 7 * SS, (235, 245, 255))
    cv.circle(648 * SS, 332 * SS, 3.5 * SS, (10, 18, 30))


def draw_spray(cv, rng):
    bx, by = 360, 640
    # 320 droplets in an upward fan at the breach.
    for _ in range(320):
        ang = math.radians(rng.uniform(-170, -10))
        dist = (rng.random() ** 1.4) * 175
        x = bx + math.cos(ang) * dist
        y = by + math.sin(ang) * dist * 0.9
        r = rng.uniform(1.5, 4.5)
        shade = rng.uniform(0.82, 1.0)
        col = (int(223 * shade), int(241 * shade), int(255 * shade))
        cv.circle(x * SS, y * SS, r * SS, col)
    # 70 sheeting droplets on the trailing edge near the tail.
    for _ in range(70):
        t = rng.uniform(0.02, 0.40)
        (x, y), r = bezier(t), body_radius(t)
        off = r + rng.uniform(2, 20)
        ang = math.radians(rng.uniform(100, 190))
        px = x + math.cos(ang) * off
        py = y + math.sin(ang) * off
        cr = rng.uniform(1.5, 4.0)
        shade = rng.uniform(0.8, 1.0)
        col = (int(223 * shade), int(241 * shade), int(255 * shade))
        cv.circle(px * SS, py * SS, cr * SS, col)


def draw_foam(cv, rng):
    for _ in range(30):
        x = rng.uniform(285, 445)
        y = rng.uniform(632, 652)
        r = rng.uniform(3, 9)
        cv.circle(x * SS, y * SS, r * SS, FOAM)


def downsample(cv):
    """Box-average the 2x buffer down to 1024x1024 scanlines."""
    out = []
    rows = cv.rows
    for oy in range(H):
        a = rows[oy * SS]
        b = rows[oy * SS + 1]
        o = bytearray(W * 3)
        for ox in range(W):
            i = ox * 6
            j = ox * 3
            o[j] = (a[i] + a[i + 3] + b[i] + b[i + 3] + 2) >> 2
            o[j + 1] = (a[i + 1] + a[i + 4] + b[i + 1] + b[i + 4] + 2) >> 2
            o[j + 2] = (a[i + 2] + a[i + 5] + b[i + 2] + b[i + 5] + 2) >> 2
        out.append(bytes(o))
    return out


def png_bytes(scanlines):
    """Encode RGB scanlines as PNG: zlib level 9, Up filter."""
    raw = bytearray()
    prev = bytes(W * 3)
    for row in scanlines:
        raw.append(2)  # filter type 2: Up
        raw += bytes((c - p) & 0xFF for c, p in zip(row, prev))
        prev = row
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def render(path):
    rng = random.Random(SEED)
    cv = Canvas()
    draw_stars(cv, rng)
    draw_halo(cv)
    draw_moon(cv)
    draw_craters(cv, rng)
    draw_path(cv, rng)
    draw_whale(cv)
    draw_belly(cv)
    draw_eye(cv)
    draw_spray(cv, rng)
    draw_foam(cv, rng)
    data = png_bytes(downsample(cv))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    print("wrote %s (%d bytes)" % (target, render(target)))

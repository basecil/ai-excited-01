"""Renderer for "The Whale That Swallowed the Moon".

Pure standard library (math / random / struct / zlib) — the grader runs
with nothing installed. The scene is painted at 2x resolution and box
downsampled to 1024x1024, then encoded to PNG by hand.

Scene: a humpback breaches out of a night sea toward a huge full moon,
its head crossing the moon's lower edge, gold rim light on its back,
spray bursting where it leaves the water, a path of moonlight on the sea.
"""

import math
import random
import struct
import zlib

SEED = 4177
SS = 2  # supersample factor
W, H = 1024, 1024
SW, SH = W * SS, H * SS

# --- palette (final-pixel coordinates unless noted) -------------------------
SKY_TOP = (2, 6, 23)
SKY_HORIZON = (11, 30, 58)
SEA_TOP = (13, 27, 51)
SEA_BOTTOM = (4, 7, 15)
MOON_CORE = (255, 251, 232)
MOON_EDGE = (238, 214, 136)
MOON_X, MOON_Y, MOON_R = 660, 270, 165
HORIZON = 640
BODY = (36, 62, 108)        # whale, above the waterline
BODY_DARK = (32, 54, 92)    # whale, submerged part
BELLY = (120, 150, 195)     # pale belly patch
RIM = (255, 212, 118)       # gold rim light
RIM_DARK = (120, 92, 44)    # rim light under water
FIN = (27, 47, 85)
SPRAY = (228, 239, 250)
FOAM = (212, 227, 243)
GOLD = (255, 203, 100)

# Whale spine: quadratic bezier, tail -> control -> head.
TAIL = (360.0, 720.0)
CTRL = (330.0, 480.0)
HEAD = (628.0, 352.0)


def mix(c1, c2, t):
    """Linear blend between two RGB colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def bezier(t):
    u = 1.0 - t
    return (
        u * u * TAIL[0] + 2.0 * u * t * CTRL[0] + t * t * HEAD[0],
        u * u * TAIL[1] + 2.0 * u * t * CTRL[1] + t * t * HEAD[1],
    )


def body_radius(t):
    """Radius profile: 18 at the tail, 95 mid-body, 44 at the head."""
    if t <= 0.55:
        return 18.0 + 77.0 * (t / 0.55) ** 0.8
    return 95.0 - 51.0 * ((t - 0.55) / 0.45) ** 1.1


class Canvas:
    """RGB bytearray canvas, drawn in final coordinates, stored at 2x."""

    def __init__(self):
        self.buf = bytearray(SW * SH * 3)

    def _row_fill(self, sy, x0, x1, color):
        """Fill supersampled row `sy` between pixel columns x0..x1."""
        if x0 >= x1:
            return
        start = (sy * SW + x0) * 3
        self.buf[start:start + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def fill_rect(self, x0, y0, x1, y1, color):
        sx0 = max(0, int(x0 * SS))
        sx1 = min(SW, int(x1 * SS))
        sy0 = max(0, int(y0 * SS))
        sy1 = min(SH, int(y1 * SS))
        for sy in range(sy0, sy1):
            self._row_fill(sy, sx0, sx1, color)

    def fill_circle(self, cx, cy, r, color):
        scx, scy, sr = cx * SS, cy * SS, r * SS
        sy0 = max(0, int(scy - sr))
        sy1 = min(SH, int(scy + sr) + 1)
        r2 = sr * sr
        for sy in range(sy0, sy1):
            dy = (sy + 0.5) - scy
            rem = r2 - dy * dy
            if rem <= 0:
                continue
            dx = math.sqrt(rem)
            x0 = max(0, int(scx - dx))
            x1 = min(SW, int(scx + dx) + 1)
            self._row_fill(sy, x0, x1, color)

    def fill_poly(self, points, color):
        """Scanline polygon fill (final coordinates)."""
        pts = [(x * SS, y * SS) for x, y in points]
        ys = [p[1] for p in pts]
        sy0 = max(0, int(min(ys)))
        sy1 = min(SH, int(max(ys)) + 1)
        n = len(pts)
        for sy in range(sy0, sy1):
            y = sy + 0.5
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self._row_fill(sy, max(0, int(xs[j])),
                               min(SW, int(xs[j + 1]) + 1), color)


def paint_sky_sea(cv):
    for sy in range(SH):
        y = sy / SS
        if y < HORIZON:
            c = mix(SKY_TOP, SKY_HORIZON, y / HORIZON)
        else:
            c = mix(SEA_TOP, SEA_BOTTOM, (y - HORIZON) / (H - HORIZON))
        cv._row_fill(sy, 0, SW, c)


def paint_stars(cv, rng):
    for _ in range(280):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 615)
        if math.hypot(x - MOON_X, y - MOON_Y) < 205:
            continue  # clear zone around the moon
        roll = rng.random()
        if roll < 0.12:
            r, c = 2.2, (255, 255, 255)
        elif roll < 0.4:
            r, c = 1.5, (222, 232, 248)
        else:
            r, c = 1.0, (190, 205, 230)
        cv.fill_circle(x, y, r, c)


def paint_moon(cv, rng):
    sky_here = mix(SKY_TOP, SKY_HORIZON, MOON_Y / HORIZON)
    # 36-ring glow halo, faintest ring outermost.
    for i in range(36, 0, -1):
        t = (36 - i) / 35.0
        cv.fill_circle(MOON_X, MOON_Y, MOON_R + i * 2.5,
                       mix(sky_here, MOON_EDGE, 0.03 + 0.30 * t))
    # Disc: concentric rings, edge color outside, pale core inside.
    steps = 24
    for i in range(steps, -1, -1):
        r = MOON_R * (i + 1) / (steps + 1)
        cv.fill_circle(MOON_X, MOON_Y, r,
                       mix(MOON_EDGE, MOON_CORE, 1.0 - r / (MOON_R + 1)))
    # 16 craters.
    for _ in range(16):
        while True:
            x = rng.uniform(MOON_X - 140, MOON_X + 140)
            y = rng.uniform(MOON_Y - 140, MOON_Y + 140)
            if math.hypot(x - MOON_X, y - MOON_Y) < 135:
                break
        cv.fill_circle(x, y, rng.uniform(4, 14), (206, 186, 116))


def paint_moon_path(cv, rng):
    def half_width(y):
        d = (y - HORIZON) / (H - HORIZON)
        return 30.0 + 130.0 * d

    # 8 gold strips, widening with depth.
    for y in (660, 700, 745, 795, 850, 905, 960, 1005):
        hw = half_width(y) * 0.85
        x = MOON_X - hw + rng.uniform(-10, 10)
        end = MOON_X + hw
        while x < end:
            seg = rng.uniform(18, 60)
            cv.fill_rect(x, y, min(x + seg, end), y + rng.uniform(4, 8),
                         (200, 158, 70))
            x += seg + rng.uniform(8, 30)
    # 420 sparkle dashes inside the wedge.
    for _ in range(420):
        y = rng.uniform(HORIZON + 5, H - 4)
        hw = half_width(y)
        x = rng.uniform(MOON_X - hw, MOON_X + hw)
        cv.fill_rect(x, y, x + rng.uniform(2, 7), y + rng.uniform(1, 2),
                     (255, 214, 120) if rng.random() < 0.5 else (232, 190, 92))


def paint_whale(cv, rng):
    spine = [(bezier(i / 28.0), body_radius(i / 28.0)) for i in range(29)]

    # Gold rim: same body shifted up-right, drawn first.
    for (x, y), r in spine:
        rim = RIM if y <= HORIZON else RIM_DARK
        cv.fill_circle(x + 17, y - 13, r, rim)
    # Body, two-tone across the waterline.
    for (x, y), r in spine:
        cv.fill_circle(x, y, r, BODY if y <= HORIZON else BODY_DARK)
    # Belly: smaller circles hugging the lower side of the body.
    for i in range(9, 23):
        (x, y), r = spine[i]
        cv.fill_circle(x, y + r * 0.30, r * 0.42, BELLY)

    # Flukes: concave polygon at the tail, gold rim on the top edge.
    flukes = [(280, 690), (330, 706), (360, 716), (390, 706), (440, 690),
              (405, 672), (360, 684), (315, 672)]
    gold = [(x, y - 3) for x, y in flukes]
    cv.fill_poly(gold, RIM_DARK)
    cv.fill_poly(flukes, BODY_DARK)

    # Pectoral fin: tapered polygon on the body's lower side.
    cv.fill_poly([(375, 545), (330, 620), (312, 668), (360, 650),
                  (415, 590)], FIN)

    # Eye: pale dot + dark pupil on the head.
    cv.fill_circle(612, 332, 7, (235, 240, 248))
    cv.fill_circle(612, 332, 3.5, (8, 12, 24))


def paint_spray_foam(cv, rng):
    bx, by = 360.0, HORIZON  # breach point
    # 320 droplets in an upward fan at the breach.
    for _ in range(320):
        ang = math.radians(rng.uniform(-165, -15))
        dist = rng.uniform(8, 190) * rng.random() ** 0.5
        x = bx + math.cos(ang) * dist
        y = by + math.sin(ang) * dist + dist * dist * 0.0016
        cv.fill_circle(x, y, rng.uniform(1.0, 3.0), SPRAY)
    # 70 sheeting droplets along the trailing edge near the waterline.
    for _ in range(70):
        t = rng.uniform(0.05, 0.35)
        (x, y), r = bezier(t), body_radius(t)
        x += rng.uniform(-r - 22, -r - 4)
        y += rng.uniform(-14, 26)
        cv.fill_circle(x, y, rng.uniform(1.0, 2.5), SPRAY)
    # 30 foam blobs at the waterline.
    for _ in range(30):
        cv.fill_circle(rng.uniform(290, 440), rng.uniform(632, 652),
                       rng.uniform(2, 7), FOAM)


def downsample(buf):
    """Box-average the 2x buffer down to 1024x1024."""
    out = bytearray(W * H * 3)
    sw3 = SW * 3
    for y in range(H):
        base0 = (2 * y) * sw3
        base1 = base0 + sw3
        o = y * W * 3
        for x in range(W):
            i0 = base0 + x * 6
            i1 = base1 + x * 6
            out[o] = (buf[i0] + buf[i0 + 3] + buf[i1] + buf[i1 + 3] + 2) >> 2
            out[o + 1] = (buf[i0 + 1] + buf[i0 + 4] + buf[i1 + 1]
                          + buf[i1 + 4] + 2) >> 2
            out[o + 2] = (buf[i0 + 2] + buf[i0 + 5] + buf[i1 + 2]
                          + buf[i1 + 5] + 2) >> 2
            o += 3
    return out


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def encode_png(rgb):
    stride = W * 3
    raw = bytearray()
    prev = bytes(stride)
    for y in range(H):
        row = bytes(rgb[y * stride:(y + 1) * stride])
        if y == 0:
            raw.append(0)
            raw += row
        else:
            raw.append(2)  # Up filter
            raw += bytes((a - b) & 0xFF for a, b in zip(row, prev))
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            _chunk(b"IEND", b""))


def render_png():
    rng = random.Random(SEED)
    cv = Canvas()
    paint_sky_sea(cv)
    paint_stars(cv, rng)
    paint_moon(cv, rng)
    paint_moon_path(cv, rng)
    paint_whale(cv, rng)
    paint_spray_foam(cv, rng)
    return encode_png(downsample(cv.buf))


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    data = render_png()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))

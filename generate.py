"""The Whale That Swallowed the Moon.

Pure-stdlib Python renderer for the make.fun ai-excited-01 entry.
Renders a 1024x1024 PNG: a whale breaching toward a full moon, flat
illustration style. No third-party dependencies -- the grader runs
standard library only.
"""

import math
import random
import struct
import zlib

SEED = 4177
W = 1024
H = 1024
SCALE = 2
RW = W * SCALE
RH = H * SCALE
HORIZON = 640

SKY_TOP = (2, 6, 23)        # #020617
SKY_HORIZON = (11, 30, 58)  # #0b1e3a
SEA_TOP = (13, 27, 51)      # #0d1b33
SEA_BOTTOM = (4, 7, 15)     # #04070f
MOON_CORE = (255, 251, 232)  # #fffbe8
MOON_EDGE = (238, 214, 136)  # #eed688
HALO_GLOW = (238, 214, 136)
GOLD = (232, 200, 90)
GOLD_BRIGHT = (245, 214, 122)
WHALE_BODY = (20, 38, 62)
WHALE_BELLY = (42, 74, 107)
SPRAY_LIGHT = (207, 230, 255)
SPRAY_MID = (168, 208, 240)
FOAM = (232, 244, 255)
EYE_PALE = (223, 234, 245)
EYE_DARK = (10, 18, 32)
CRATER = (224, 200, 140)
CRATER_SHADOW = (210, 184, 120)

MOON_C = (660, 270)
MOON_R = 165


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def sky_color(y):
    return lerp_color(SKY_TOP, SKY_HORIZON, max(0.0, min(1.0, y / HORIZON)))


def sea_color(y):
    return lerp_color(SEA_TOP, SEA_BOTTOM,
                      max(0.0, min(1.0, (y - HORIZON) / (H - HORIZON))))


class Canvas:
    """RGB bytearray canvas with scanline fill primitives."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def vgrad(self, y0, y1, c_top, c_bottom):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            t = (y - y0) / max(1, y1 - y0)
            c = lerp_color(c_top, c_bottom, t)
            i0 = y * self.w * 3
            self.buf[i0:i0 + self.w * 3] = bytes(c) * self.w

    def circle(self, cx, cy, r, color):
        r = int(round(r))
        if r <= 0:
            return
        cx = int(round(cx))
        cy = int(round(cy))
        r2 = r * r
        row = bytes(color)
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            dx = int(math.sqrt(max(0, r2 - dy * dy)))
            x0 = max(0, cx - dx)
            x1 = min(self.w - 1, cx + dx)
            if x1 >= x0:
                i0 = (y * self.w + x0) * 3
                self.buf[i0:(y * self.w + x1 + 1) * 3] = row * (x1 - x0 + 1)

    def halo_ring(self, cx, cy, r, alpha):
        """Filled circle blended row-by-row toward gold from the local
        background gradient (sky above the horizon, sea below), so the
        glow has no visible edge."""
        r = int(round(r))
        if r <= 0:
            return
        cx = int(round(cx))
        cy = int(round(cy))
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            dx = int(math.sqrt(max(0, r2 - dy * dy)))
            x0 = max(0, cx - dx)
            x1 = min(self.w - 1, cx + dx)
            if x1 >= x0:
                fy = y / SCALE
                base = sky_color(fy) if fy < HORIZON else sea_color(fy)
                c = lerp_color(base, HALO_GLOW, alpha)
                row = bytes(c) * (x1 - x0 + 1)
                i0 = (y * self.w + x0) * 3
                self.buf[i0:(y * self.w + x1 + 1) * 3] = row

    def rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(round(x0)))
        y0 = max(0, int(round(y0)))
        x1 = min(self.w - 1, int(round(x1)))
        y1 = min(self.h - 1, int(round(y1)))
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i0 = (y * self.w + x0) * 3
            self.buf[i0:i0 + len(row)] = row

    def polygon(self, pts, color):
        ymin = max(0, min(int(p[1]) for p in pts))
        ymax = min(self.h - 1, max(int(math.ceil(p[1])) for p in pts))
        n = len(pts)
        row = bytes(color)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                x0 = max(0, int(math.ceil(xs[j])))
                x1 = min(self.w - 1, int(math.floor(xs[j + 1])))
                if x1 >= x0:
                    i0 = (y * self.w + x0) * 3
                    self.buf[i0:(y * self.w + x1 + 1) * 3] = row * (x1 - x0 + 1)


def _bez(p0, p1, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def _bez_deriv(p0, p1, p2, t):
    return (2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]),
            2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]))


def _whale_radius(t):
    if t < 0.65:
        return 18 + (95 - 18) * (t / 0.65) ** 0.9
    return 95 - (95 - 44) * ((t - 0.65) / 0.35) ** 1.1


def render():
    rng = random.Random(SEED)
    cv = Canvas(RW, RH)
    S = SCALE

    # Sky and sea gradients.
    cv.vgrad(0, HORIZON * S - 1, SKY_TOP, SKY_HORIZON)
    cv.vgrad(HORIZON * S, RH - 1, SEA_TOP, SEA_BOTTOM)

    # Stars: 280, with a clear zone around the moon.
    placed = 0
    while placed < 280:
        x = rng.uniform(0, W)
        y = rng.uniform(0, 600)
        if (x - MOON_C[0]) ** 2 + (y - MOON_C[1]) ** 2 < 215 ** 2:
            continue
        r = rng.choice([1, 1, 1, 2, 2, 3])
        b = rng.uniform(0.55, 1.0)
        c = (int(200 + 55 * b), int(210 + 45 * b), 255)
        cv.circle(x * S, y * S, r * S, c)
        if r == 3 and rng.random() < 0.5:
            cv.rect((x - 5) * S, (y - 0.5) * S, (x + 5) * S, (y + 0.5) * S, c)
            cv.rect((x - 0.5) * S, (y - 5) * S, (x + 0.5) * S, (y + 5) * S, c)
        placed += 1

    # Moon glow halo: 36 rings, faintest outside. Each ring is matched
    # row-by-row to the local background gradient so no disc edge shows.
    for i in range(36):
        radius = (MOON_R + (36 - i) * 6) * S
        alpha = 0.02 + 0.30 * (i / 35.0) ** 1.5
        cv.halo_ring(MOON_C[0] * S, MOON_C[1] * S, radius, alpha)

    # Moon disc: radial gradient, edge to core.
    rings = 48
    for i in range(rings):
        frac = i / (rings - 1)
        radius = MOON_R * (1.0 - frac * 0.96) * S
        c = lerp_color(MOON_EDGE, MOON_CORE, frac)
        cv.circle(MOON_C[0] * S, MOON_C[1] * S, radius, c)

    # 16 craters.
    for _ in range(16):
        while True:
            a = rng.uniform(0, 2 * math.pi)
            d = math.sqrt(rng.uniform(0, 1)) * MOON_R * 0.82
            cx = MOON_C[0] + math.cos(a) * d
            cy = MOON_C[1] + math.sin(a) * d
            if (cx - MOON_C[0]) ** 2 + (cy - MOON_C[1]) ** 2 < (MOON_R * 0.82) ** 2:
                break
        cr = rng.uniform(6, 18)
        cv.circle(cx * S, cy * S, cr * S, CRATER)
        cv.circle((cx - cr * 0.25) * S, (cy - cr * 0.25) * S,
                  cr * 0.7 * S, CRATER_SHADOW)

    # Moonlight path: 8 gold strips, widening with depth.
    for i in range(8):
        t = i / 7.0
        y = 660 + t * 330
        w_top = 60 + t * 160
        w_bot = w_top + 26
        h = 7 + t * 5
        alpha = 0.72 - 0.38 * t
        c = lerp_color(sea_color(y), GOLD_BRIGHT, alpha)
        cv.polygon([
            ((MOON_C[0] - w_top / 2) * S, y * S),
            ((MOON_C[0] + w_top / 2) * S, y * S),
            ((MOON_C[0] + w_bot / 2) * S, (y + h) * S),
            ((MOON_C[0] - w_bot / 2) * S, (y + h) * S),
        ], c)

    # 420 sparkle dashes along the path, widening with depth.
    for _ in range(420):
        y = rng.uniform(650, 1020)
        spread = 45 + (y - 650) / 370.0 * 190
        x = MOON_C[0] + rng.uniform(-spread, spread)
        ln = rng.uniform(4, 18)
        ht = rng.uniform(1.5, 3.5)
        alpha = rng.uniform(0.25, 0.8)
        c = lerp_color(sea_color(y), GOLD_BRIGHT, alpha)
        cv.rect((x - ln / 2) * S, (y - ht / 2) * S,
                (x + ln / 2) * S, (y + ht / 2) * S, c)

    # Whale: union of 29 circles along a quadratic bezier spine.
    P0 = (360, 720)
    P1 = (330, 480)
    P2 = (628, 352)
    spine = []
    for i in range(29):
        t = i / 28.0
        spine.append((_bez(P0, P1, P2, t), _whale_radius(t)))

    # Gold rim light: same body shifted (+17, -13), drawn first.
    for (x, y), r in spine:
        cv.circle((x + 17) * S, (y - 13) * S, r * S, GOLD)
    # Body.
    for (x, y), r in spine:
        cv.circle(x * S, y * S, r * S, WHALE_BODY)
    # Belly: lighter patch clipped to the body (offset + smaller radius).
    for i, ((x, y), r) in enumerate(spine):
        t = i / 28.0
        if 0.12 < t < 0.92:
            cv.circle((x + r * 0.15) * S, (y + r * 0.30) * S,
                      r * 0.62 * S, WHALE_BELLY)

    # Flukes: concave notched fan at the tail, gold top rim.
    fluke = [(344, 706), (270, 760), (320, 745), (360, 732),
             (400, 745), (450, 760), (376, 706)]
    gold_fluke = [(x, y - 3) for x, y in fluke]
    cv.polygon([(x * S, y * S) for x, y in gold_fluke], GOLD)
    cv.polygon([(x * S, y * S) for x, y in fluke], WHALE_BELLY)

    # Pectoral fin: tapered triangle sticking out of the body's lower
    # edge, in belly color (shadow side, no gold rim).
    fin = [(395, 535), (365, 570), (440, 560)]
    cv.polygon([(x * S, y * S) for x, y in fin], WHALE_BELLY)

    # Eye: pale dot + dark pupil at the head.
    cv.circle(648 * S, 332 * S, 7 * S, EYE_PALE)
    cv.circle(648 * S, 332 * S, 3.5 * S, EYE_DARK)

    # Spray: 320 droplets in an upward fan at the breach.
    bx, by = 359, 640
    for _ in range(320):
        ang = math.radians(rng.uniform(-160, -20))
        dist = 15 + (rng.random() ** 1.6) * 205
        x = bx + math.cos(ang) * dist
        y = by + math.sin(ang) * dist
        r = max(0.8, rng.uniform(1, 4) * (1 - dist / 260))
        c = SPRAY_LIGHT if rng.random() < 0.6 else SPRAY_MID
        cv.circle(x * S, y * S, r * S, c)

    # 70 sheeting droplets on the trailing (lower) edge.
    for _ in range(70):
        t = rng.uniform(0.08, 0.62)
        (x, y) = _bez(P0, P1, P2, t)
        dx, dy = _bez_deriv(P0, P1, P2, t)
        n = math.hypot(dx, dy) or 1.0
        px, py = -dy / n, dx / n
        if py < 0:
            px, py = -px, -py
        r = _whale_radius(t)
        off = r * rng.uniform(0.85, 1.15)
        cx = x + px * off + rng.uniform(-6, 6)
        cy = y + py * off + rng.uniform(-6, 6)
        cv.circle(cx * S, cy * S, rng.uniform(1, 3) * S,
                  SPRAY_LIGHT if rng.random() < 0.5 else SPRAY_MID)

    # Foam: 30 small blobs at the waterline.
    for _ in range(30):
        cx = rng.uniform(270, 460)
        cy = rng.uniform(630, 660)
        r = rng.uniform(4, 9)
        cv.circle(cx * S, cy * S, r * S, FOAM)
        cv.circle((cx + rng.uniform(-r, r)) * S,
                  (cy + rng.uniform(-r * 0.5, r * 0.5)) * S,
                  r * rng.uniform(0.4, 0.6) * S, FOAM)

    return cv


def _downsample(src, w2, h2):
    w, h = w2 // 2, h2 // 2
    out = bytearray(w * h * 3)
    for y in range(h):
        sy = y * 2
        row0 = sy * w2 * 3
        row1 = (sy + 1) * w2 * 3
        for x in range(w):
            sx = x * 2 * 3
            i00 = row0 + sx
            i01 = i00 + 3
            i10 = row1 + sx
            i11 = i10 + 3
            o = (y * w + x) * 3
            out[o] = (src[i00] + src[i01] + src[i10] + src[i11]) >> 2
            out[o + 1] = (src[i00 + 1] + src[i01 + 1] + src[i10 + 1] + src[i11 + 1]) >> 2
            out[o + 2] = (src[i00 + 2] + src[i01 + 2] + src[i10 + 2] + src[i11 + 2]) >> 2
    return out


def _encode_png(rgb, w, h):
    raw = bytearray()
    prev = bytes(w * 3)
    stride = w * 3
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        raw.append(2)  # Up filter
        raw.extend((row[i] - prev[i]) & 0xFF for i in range(stride))
        prev = bytes(row)
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def render_png():
    cv = render()
    small = _downsample(cv.buf, RW, RH)
    return _encode_png(small, W, H)

"""The Whale That Swallowed the Moon.

A pure-standard-library renderer: draws a whale breaching out of a night
sea to swallow the full moon, and encodes the result as a PNG.

The grading sandbox runs Python with the standard library only, so every
pixel here is computed with math, random, struct and zlib -- no Pillow,
no numpy, no network. The scene is rendered at 2x and box-downsampled,
which antialiases every edge without per-pixel distance fields.

Deterministic: one fixed seed drives every random choice, the PNG encoder
writes no timestamps, and zlib output is a pure function of its input, so
two runs produce byte-identical files.
"""

import math
import random
import struct
import zlib

SEED = 4177

# Final image size. The scene is drawn at SSx and downsampled.
W, H = 1024, 1024
SS = 2
SW, SH = W * SS, H * SS

HORIZON = 640 * SS  # the sea starts here (supersampled coordinates)
MOON_C = (660 * SS, 270 * SS)
MOON_R = 165 * SS

SKY_TOP = (2, 6, 23)
SKY_HORIZON = (11, 30, 58)
SEA_TOP = (13, 27, 51)
SEA_BOTTOM = (4, 7, 15)
MOON_CORE = (255, 251, 232)
MOON_EDGE = (238, 214, 136)
MOON_GLOW = (247, 224, 150)
WHALE = (6, 13, 24)
WHALE_BELLY = (26, 47, 71)
RIM = (242, 212, 136)
SPRAY = (234, 244, 255)
GOLD = (247, 220, 138)


def lerp(a, b, t):
    """Linear interpolation between two RGB colors."""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def blend(fg, bg, alpha):
    """Alpha-composite fg (alpha 0..255) over bg; both RGB tuples."""
    inv = 255 - alpha
    return tuple((fg[i] * alpha + bg[i] * inv) // 255 for i in range(3))


class Canvas:
    """An RGB bytearray with fast horizontal-span fills."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def hspan(self, y, x0, x1, color):
        """Fill the solid horizontal span [x0, x1) on row y, clipped."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w, int(x1))
        if x1 <= x0:
            return
        n = x1 - x0
        off = y * self.w * 3 + x0 * 3
        self.buf[off:off + n * 3] = bytes(color) * n

    def plot(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            off = (y * self.w + x) * 3
            self.buf[off:off + 3] = bytes(color)

    def blend_plot(self, x, y, color, alpha):
        if 0 <= x < self.w and 0 <= y < self.h:
            off = (y * self.w + x) * 3
            inv = 255 - alpha
            b = self.buf
            b[off] = (color[0] * alpha + b[off] * inv) // 255
            b[off + 1] = (color[1] * alpha + b[off + 1] * inv) // 255
            b[off + 2] = (color[2] * alpha + b[off + 2] * inv) // 255


def circle_intervals(cx, cy, r, y):
    """The x-interval [x0, x1) of circle (cx, cy, r) on row y, or None."""
    dy = y - cy
    if abs(dy) >= r:
        return None
    dx = int(math.sqrt(r * r - dy * dy))
    return (cx - dx, cx + dx + 1)


def fill_circle(cv, cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        iv = circle_intervals(cx, cy, r, y)
        if iv:
            cv.hspan(y, iv[0], iv[1], color)


def fill_circle_alpha(cv, cx, cy, r, color, alpha):
    for y in range(cy - r, cy + r + 1):
        iv = circle_intervals(cx, cy, r, y)
        if iv:
            for x in range(iv[0], iv[1]):
                cv.blend_plot(x, y, color, alpha)


def fill_polygon(cv, points, color):
    """Scanline polygon fill (even-odd rule), for concave shapes too."""
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            cv.hspan(y, int(xs[j]), int(xs[j + 1]) + 1, color)


# ---------------------------------------------------------------- spine
# The whale's backbone is a quadratic bezier from the tail stock, still
# at the water, up to the head biting at the moon. The body is the union
# of circles along it, fat in the middle, tapering to tail and snout.

SPINE = ((360 * SS, 720 * SS), (330 * SS, 480 * SS), (628 * SS, 352 * SS))

# Radius profile along the spine: (t, radius in supersampled pixels).
SPINE_R = [(0.00, 36), (0.15, 90), (0.30, 140), (0.50, 175),
           (0.70, 195), (0.85, 160), (0.95, 115), (1.00, 88)]


def bezier(p0, c, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1])


def spine_radius(t):
    for i in range(len(SPINE_R) - 1):
        t0, r0 = SPINE_R[i]
        t1, r1 = SPINE_R[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            return r0 + (r1 - r0) * f
    return SPINE_R[-1][1]


def body_intervals(spine, n=28):
    """Union of circles along a spine -> {row: [(x0, x1), ...]} merged."""
    rows = {}
    for i in range(n + 1):
        t = i / n
        cx, cy = bezier(spine[0], spine[1], spine[2], t)
        r = int(round(spine_radius(t)))
        cx = int(round(cx))
        cy = int(round(cy))
        for y in range(cy - r, cy + r + 1):
            iv = circle_intervals(cx, cy, r, y)
            if iv:
                rows.setdefault(y, []).append(iv)
    for y, ivs in rows.items():
        ivs.sort()
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                if b > merged[-1][1]:
                    merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
        rows[y] = merged
    return rows


# ------------------------------------------------------------------ sky

def sky_color(y):
    return lerp(SKY_TOP, SKY_HORIZON, y / HORIZON)


def sea_color(y):
    return lerp(SEA_TOP, SEA_BOTTOM, (y - HORIZON) / (SH - HORIZON))


def draw_sky(cv):
    for y in range(HORIZON):
        cv.hspan(y, 0, SW, sky_color(y))


def draw_cloud(cv, cx, cy, a, b, color, alpha):
    """A thin, dark, translucent elliptical streak (sky only)."""
    for y in range(cy - b, cy + b + 1):
        if y < 0 or y >= HORIZON:
            continue
        dy = (y - cy) / b
        if abs(dy) >= 1:
            continue
        dx = int(a * math.sqrt(1 - dy * dy))
        cv.hspan(y, cx - dx, cx + dx + 1, blend(color, sky_color(y), alpha))


def draw_glow(cv):
    """The moon's halo: concentric annuli, each a constant composite."""
    cx, cy = MOON_C
    r_out = MOON_R + 510
    rings = 36
    for k in range(rings):
        r_outer = r_out - (r_out - MOON_R) * k / rings
        r_inner = r_out - (r_out - MOON_R) * (k + 1) / rings
        mid = (r_outer + r_inner) / 2
        frac = (r_out - mid) / (r_out - MOON_R)
        alpha = int(88 * frac ** 1.6)
        if alpha <= 0:
            continue
        y0 = max(0, int(cy - r_outer))
        y1 = min(SH - 1, int(cy + r_outer))
        for y in range(y0, y1 + 1):
            dy = y - cy
            if abs(dy) >= r_outer:
                continue
            dx_o = math.sqrt(r_outer * r_outer - dy * dy)
            if abs(dy) < r_inner:
                dx_i = math.sqrt(r_inner * r_inner - dy * dy)
            else:
                dx_i = 0.0
            base = sky_color(y) if y < HORIZON else sea_color(y)
            col = blend(MOON_GLOW, base, alpha)
            cv.hspan(y, int(cx - dx_o), int(cx - dx_i) + 1, col)
            cv.hspan(y, int(cx + dx_i), int(cx + dx_o) + 1, col)


# Moon radial gradient, precomputed by r^2 bucket (0 = centre, 1 = rim).
def _moon_table():
    table = []
    for b in range(257):
        f = b / 256
        c = lerp(MOON_CORE, MOON_EDGE, f ** 1.4)
        if f > 0.965:  # slight limb darkening at the very rim
            c = blend((190, 175, 130), c, int(160 * (f - 0.965) / 0.035))
        table.append(c)
    return table


MOON_TABLE = _moon_table()


def draw_moon(cv):
    cx, cy = MOON_C
    r = MOON_R
    r2max = r * r
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        dy2 = dy * dy
        if dy2 >= r2max:
            continue
        dx = int(math.sqrt(r2max - dy2))
        off = (y * SW + (cx - dx)) * 3
        for x in range(cx - dx, cx + dx + 1):
            ddx = x - cx
            b = (ddx * ddx + dy2) * 256 // r2max
            cv.buf[off:off + 3] = bytes(MOON_TABLE[b])
            off += 3


def draw_craters(cv, rng):
    cx, cy = MOON_C
    r = MOON_R
    for _ in range(16):
        ang = rng.uniform(0, 2 * math.pi)
        rr = r * 0.78 * math.sqrt(rng.random())
        ccx = int(cx + rr * math.cos(ang))
        ccy = int(cy + rr * math.sin(ang))
        cr = rng.randint(10, 42)
        d2 = (ccx - cx) ** 2 + (ccy - cy) ** 2
        b = min(256, d2 * 256 // (r * r))
        col = blend((217, 196, 138), MOON_TABLE[b], 70)
        for y in range(ccy - cr, ccy + cr + 1):
            iv = circle_intervals(ccx, ccy, cr, y)
            moon_iv = circle_intervals(cx, cy, r, y)
            if iv and moon_iv:
                x0, x1 = max(iv[0], moon_iv[0]), min(iv[1], moon_iv[1])
                if x1 > x0:
                    cv.hspan(y, x0, x1, col)


# ------------------------------------------------------------------ sea

def draw_sea(cv):
    for y in range(HORIZON, SH):
        cv.hspan(y, 0, SW, sea_color(y))
    # a band of moonlit haze right at the horizon
    for y in range(HORIZON, HORIZON + 26):
        t = 1 - (y - HORIZON) / 26
        cv.hspan(y, 0, SW, blend((28, 58, 92), sea_color(y), int(70 * t)))


def draw_moonlight(cv):
    """The moon's golden path on the water, widening toward the viewer."""
    cx = MOON_C[0]
    strips = 8
    for y in range(HORIZON + 4, SH):
        depth = (y - HORIZON) / (SH - HORIZON)
        hw = int(130 + depth * 260)
        base = sea_color(y)
        for s in range(strips):
            f0 = s / strips
            f1 = (s + 1) / strips
            mid = (f0 + f1) / 2
            alpha = int(64 * (math.cos(mid * math.pi / 2) ** 1.5)
                        * (0.55 + 0.45 * depth))
            if alpha <= 0:
                continue
            col = blend(GOLD, base, alpha)
            cv.hspan(y, int(cx + f0 * hw), int(cx + f1 * hw), col)
            cv.hspan(y, int(cx - f1 * hw), int(cx - f0 * hw), col)


def draw_dashes(cv, rng):
    """Glittering sparkles in the moon path, plus sparse wave streaks."""
    cx = MOON_C[0]
    for _ in range(420):
        y = rng.randint(HORIZON + 6, SH - 8)
        depth = (y - HORIZON) / (SH - HORIZON)
        hw = int((130 + depth * 260) * (0.35 + 0.65 * rng.random()))
        x = int(cx + rng.uniform(-hw, hw))
        ln = rng.randint(12, 110)
        br = rng.randint(120, 255)
        col = (min(255, 200 + br // 3), min(255, 170 + br // 4),
               90 + br // 3)
        cv.hspan(y, x, x + ln, col)
        if rng.random() < 0.5:
            cv.hspan(y + 1, x, x + ln, col)
    for _ in range(240):
        y = rng.randint(HORIZON + 10, SH - 6)
        x = rng.randint(0, SW - 160)
        ln = rng.randint(20, 150)
        cv.hspan(y, x, x + ln, lerp((16, 38, 66), (40, 80, 120),
                                    rng.random()))
    # a few dim sparkles on the open sea, left of the moon path
    for _ in range(60):
        y = rng.randint(HORIZON + 10, SH - 6)
        x = rng.randint(0, 900)
        ln = rng.randint(10, 60)
        cv.hspan(y, x, x + ln, lerp((20, 44, 74), (60, 100, 140),
                                    rng.random()))


def draw_stars(cv, rng):
    cx, cy = MOON_C
    clear2 = (MOON_R + 260) ** 2  # keep the moon's glow clear of stars
    for _ in range(280):
        x = rng.randint(0, SW - 1)
        y = rng.randint(0, HORIZON - 20)
        if (x - cx) ** 2 + (y - cy) ** 2 < clear2:
            continue
        roll = rng.random()
        if roll < 0.72:
            cv.plot(x, y, (220, 230, 245))
            if rng.random() < 0.4:
                cv.plot(x + 1, y, (200, 214, 235))
        elif roll < 0.94:
            c = (235, 242, 255)
            cv.plot(x, y, c)
            cv.plot(x + 1, y, c)
            cv.plot(x, y + 1, c)
            cv.plot(x + 1, y + 1, c)
            cv.plot(x - 1, y, (180, 195, 220))
            cv.plot(x + 2, y, (180, 195, 220))
        else:
            # a bright star with a cross sparkle
            c = (255, 255, 255)
            arm = rng.randint(8, 18)
            for d in range(-arm, arm + 1):
                a = 255 - int(200 * abs(d) / arm)
                cv.blend_plot(x + d, y, c, a)
                cv.blend_plot(x, y + d, c, a)
            cv.plot(x, y, c)


# ---------------------------------------------------------------- whale

def draw_whale(cv):
    """Moonlit rim first (body shifted toward the moon), then the body."""
    rim_spine = tuple((x + 34, y - 26) for x, y in SPINE)
    for y, ivs in body_intervals(rim_spine).items():
        for a, b in ivs:
            cv.hspan(y, a, b, RIM)
    rows = body_intervals(SPINE)
    for y, ivs in rows.items():
        for a, b in ivs:
            cv.hspan(y, a, b, WHALE)
    return rows


def draw_belly(cv, body_rows):
    """A lighter patch along the underside, clipped to the body."""
    belly_spine = tuple((x - 30, y + 55) for x, y in SPINE)
    for y, ivs in body_intervals(belly_spine).items():
        if y not in body_rows:
            continue
        for a, b in ivs:
            for c0, c1 in body_rows[y]:
                x0, x1 = max(a, c0), min(b, c1)
                if x1 > x0:
                    cv.hspan(y, x0, x1, WHALE_BELLY)


def draw_flukes(cv):
    fluke = [(720, 1470), (430, 1300), (560, 1405), (720, 1385),
             (880, 1405), (1010, 1310), (720, 1470)]
    rim = [(x, y - 12) for x, y in fluke]
    fill_polygon(cv, rim, RIM)
    fill_polygon(cv, fluke, WHALE)


def draw_fin(cv):
    fin = [(790, 1020), (560, 1410), (660, 1435), (850, 1120)]
    fill_polygon(cv, fin, WHALE)


def draw_eye(cv):
    fill_circle(cv, 1280, 660, 10, (223, 233, 245))
    fill_circle(cv, 1282, 662, 5, (10, 16, 28))


def draw_spray(cv, rng):
    # the burst where the whale left the water: an upward fan
    for _ in range(320):
        ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
        dist = rng.uniform(20, 360) * (0.4 + 0.6 * rng.random())
        x = int(720 + dist * math.cos(ang) * 1.4)
        y = int(1300 + dist * math.sin(ang))
        fill_circle_alpha(cv, x, y, rng.randint(2, 6), SPRAY,
                          rng.randint(140, 255))
    # water sheeting off the rising body's trailing edge
    for _ in range(70):
        t = rng.random()
        sx, sy = bezier(SPINE[0], SPINE[1], SPINE[2], t)
        nx = int(sx + rng.uniform(-200, 40))
        ny = int(sy + rng.uniform(30, 160))
        fill_circle_alpha(cv, nx, ny, rng.randint(1, 4), SPRAY,
                          rng.randint(90, 170))


def draw_foam(cv, rng):
    for _ in range(30):
        x = int(rng.gauss(720, 190))
        y = int(HORIZON + rng.gauss(30, 26))
        fill_circle_alpha(cv, x, y, rng.randint(6, 22), SPRAY,
                          rng.randint(130, 210))


# ------------------------------------------------------------- encoding

def downsample(cv):
    """Box-average the 2x canvas down to the final size."""
    out = bytearray(W * H * 3)
    src = cv.buf
    for y in range(H):
        s0 = (y * 2) * SW * 3
        s1 = (y * 2 + 1) * SW * 3
        d0 = y * W * 3
        for x in range(W):
            o = d0 + x * 3
            i0 = s0 + x * 6
            i1 = s1 + x * 6
            out[o] = (src[i0] + src[i0 + 3] + src[i1] + src[i1 + 3]) // 4
            out[o + 1] = (src[i0 + 1] + src[i0 + 4] + src[i1 + 1]
                          + src[i1 + 4]) // 4
            out[o + 2] = (src[i0 + 2] + src[i0 + 5] + src[i1 + 2]
                          + src[i1 + 5]) // 4
    return bytes(out)


def _chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def encode_png(rgb, w=W, h=H):
    """Encode raw RGB bytes as a PNG (Up filter, zlib level 9)."""
    stride = w * 3
    raw = bytearray()
    prev = bytes(stride)
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        raw.append(2)  # Up filter
        raw += bytes((row[i] - prev[i]) & 0xFF for i in range(stride))
        prev = row
    comp = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    return png


def render():
    """Draw the scene and return the finished PNG bytes."""
    rng = random.Random(SEED)
    cv = Canvas(SW, SH)
    draw_sky(cv)
    draw_sea(cv)
    draw_cloud(cv, 420, 210, 420, 34, (4, 10, 28), 70)
    draw_cloud(cv, 1620, 880, 360, 26, (4, 10, 28), 55)
    draw_glow(cv)
    draw_moon(cv)
    draw_craters(cv, rng)
    draw_moonlight(cv)
    draw_dashes(cv, rng)
    draw_stars(cv, rng)
    body_rows = draw_whale(cv)
    draw_belly(cv, body_rows)
    draw_flukes(cv)
    draw_fin(cv)
    draw_eye(cv)
    draw_spray(cv, rng)
    draw_foam(cv, rng)
    return encode_png(downsample(cv))

"""The Whale That Swallowed the Moon — pure-stdlib renderer.

Renders a 1024x1024 PNG: a whale breaching in front of a full moon over a
moonlit sea. Pure standard library only (the grader installs nothing).
Deterministic: fixed seed, no time / hash / dict-order dependence.
"""
import math
import random
import struct
import zlib

SEED = 4177
S = 2  # supersample factor
W = 1024
H = 1024
W2 = W * S
H2 = H * S
HORIZON = 640  # final px; horizon line y

SKY_TOP = (2, 6, 23)        # #020617
SKY_HORIZON = (11, 30, 58)  # #0b1e3a
SEA_TOP = (13, 27, 51)      # #0d1b33
SEA_BOTTOM = (4, 7, 15)     # #04070f
MOON_CORE = (255, 251, 232)  # #fffbe8
MOON_EDGE = (238, 214, 136)  # #eed688
GOLD = (232, 201, 106)
BODY = (22, 40, 61)
BELLY = (42, 74, 106)
FIN = (26, 46, 68)
FOAM = (235, 242, 250)
SPRAY = (220, 232, 245)


def lerp(a, b, t):
    return (int(round(a[0] + (b[0] - a[0]) * t)),
            int(round(a[1] + (b[1] - a[1]) * t)),
            int(round(a[2] + (b[2] - a[2]) * t)))


class Canvas:
    """Flat RGB bytearray with fast row-span primitives."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def hline(self, y, x0, x1, color):
        if y < 0 or y >= self.h:
            return
        if x0 < 0:
            x0 = 0
        if x1 > self.w - 1:
            x1 = self.w - 1
        if x1 < x0:
            return
        start = (y * self.w + x0) * 3
        n = x1 - x0 + 1
        self.buf[start:start + n * 3] = bytes(color) * n

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.hline(y, x0, x1, color)

    def fill_circle(self, cx, cy, r, color):
        if r <= 0:
            return
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            dx = int(math.sqrt(r2 - dy * dy))
            self.hline(y, cx - dx, cx + dx, color)

    def fill_polygon(self, pts, color):
        # even-odd scanline fill; pts = list of (x, y)
        if not pts:
            return
        ymin = max(0, min(p[1] for p in pts))
        ymax = min(self.h - 1, max(p[1] for p in pts))
        n = len(pts)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(y, int(math.ceil(xs[i])), int(math.floor(xs[i + 1])), color)


def bezier(p0, p1, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def body_radius(t):
    # radius profile (final px): 18 at tail -> 95 mid -> 44 at head
    if t <= 0.55:
        s = 0.5 - 0.5 * math.cos(math.pi * t / 0.55)
        return 18 + (95 - 18) * s
    s = 0.5 - 0.5 * math.cos(math.pi * (t - 0.55) / 0.45)
    return 95 - (95 - 44) * s


def render():
    rng = random.Random(SEED)
    cv = Canvas(W2, H2)
    hz = HORIZON * S

    # --- sky + sea gradients (per-row fills) ---
    for y in range(0, hz):
        cv.hline(y, 0, W2 - 1, lerp(SKY_TOP, SKY_HORIZON, y / (hz - 1)))
    for y in range(hz, H2):
        cv.hline(y, 0, W2 - 1, lerp(SEA_TOP, SEA_BOTTOM, (y - hz) / (H2 - hz - 1)))

    # --- stars: 280, clear zone around the moon ---
    mx, my, mr = 660 * S, 270 * S, 165 * S
    clear2 = (mr + 80) ** 2
    placed = 0
    while placed < 280:
        x = rng.randrange(0, W2)
        y = rng.randrange(0, hz)
        dx, dy = x - mx, y - my
        if dx * dx + dy * dy < clear2:
            continue
        r = rng.choice([1, 1, 2, 2, 3])
        b = rng.randrange(180, 256)
        cv.fill_circle(x, y, r, (b, b, min(255, b + 10)))
        placed += 1

    # --- moon halo: 36 rings fading outward ---
    halo_outer = lerp(SKY_TOP, SKY_HORIZON, my / hz)
    halo_inner = (235, 225, 185)
    for i in range(36, 0, -1):
        t = 1.0 - i / 36.0
        cv.fill_circle(mx, my, mr + i * 4, lerp(halo_outer, halo_inner, t * t))

    # --- moon disc: radial gradient, core bright -> edge gold ---
    steps = 24
    for i in range(steps, 0, -1):
        cv.fill_circle(mx, my, mr * i // steps,
                       lerp(MOON_CORE, MOON_EDGE, i / steps))

    # --- 16 craters ---
    for _ in range(16):
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(0, mr * 0.8)
        x = int(mx + dist * math.cos(ang))
        y = int(my + dist * math.sin(ang))
        r = rng.randrange(6, 21)
        cv.fill_circle(x, y, r, (208, 188, 128))

    # --- moonlight path: 8 gold strips, widening with depth ---
    for i in range(8):
        band0 = hz + int((H2 - hz) * i / 8)
        band1 = hz + int((H2 - hz) * (i + 1) / 8)
        bh = band1 - band0
        y0 = band0 + int(bh * 0.22)
        y1 = band1 - int(bh * 0.22)
        mid = (y0 + y1) // 2
        sea = lerp(SEA_TOP, SEA_BOTTOM, (mid - hz) / (H2 - hz))
        col = lerp(sea, (210, 180, 95), 0.15)
        half = (50 + i * 38) * S
        cv.fill_rect(mx - half, y0, mx + half, y1, col)

    # --- 420 sparkle dashes on the path ---
    for _ in range(420):
        y = rng.randrange(hz, H2)
        depth = (y - hz) / (H2 - hz)
        half = int((50 + depth * 315) * S)
        x = mx + rng.randrange(-half, half + 1)
        w = int(rng.randrange(4, 25) * (0.4 + 0.6 * depth)) * S
        h = rng.randrange(2, 5) * S
        b = rng.randrange(150, 256)
        cv.fill_rect(x - w // 2, y - h // 2, x + w // 2, y + h // 2,
                     (b, int(b * 0.9), int(b * 0.6)))

    # --- whale: 29 circles along a quadratic bezier spine ---
    p0 = (360 * S, 720 * S)
    p1 = (330 * S, 480 * S)
    p2 = (628 * S, 352 * S)
    spine = []
    for i in range(29):
        t = i / 28.0
        x, y = bezier(p0, p1, p2, t)
        spine.append((x, y, body_radius(t) * S))
    # gold rim light: same body shifted (+17,-13) final px, drawn first
    for (x, y, r) in spine:
        cv.fill_circle(int(x + 17 * S), int(y - 13 * S), int(r), GOLD)
    # body
    for (x, y, r) in spine:
        cv.fill_circle(int(x), int(y), int(r), BODY)
    # belly: lighter patch clipped to the body
    for (x, y, r) in spine:
        cv.fill_circle(int(x), int(y + r * 0.25), int(r * 0.5), BELLY)

    # --- flukes: concave hexagon at the tail, gold top rim ---
    fluke = [(355, 730), (290, 700), (300, 665), (360, 700), (420, 665), (430, 700), (365, 730)]
    fluke2 = [(x * S, y * S) for (x, y) in fluke]
    cv.fill_polygon([(x, y - 6 * S) for (x, y) in fluke2], GOLD)
    cv.fill_polygon(fluke2, BODY)

    # --- pectoral fin: tapered polygon ---
    fin = [(485, 455), (445, 530), (430, 570), (465, 555), (505, 490)]
    cv.fill_polygon([(x * S, y * S) for (x, y) in fin], FIN)

    # --- eye: pale dot + dark pupil at the head ---
    ex, ey = 640 * S, 340 * S
    cv.fill_circle(ex, ey, 4 * S, (235, 240, 245))
    cv.fill_circle(ex, ey, 2 * S, (5, 8, 12))

    # --- spray: 320 droplets in an upward fan at the breach ---
    bx, by = 360 * S, 640 * S
    for _ in range(320):
        ang = math.radians(rng.uniform(-160, -20))
        dist = rng.uniform(10, 220) * S
        x = int(bx + dist * math.cos(ang))
        y = int(by + dist * math.sin(ang))
        cv.fill_circle(x, y, rng.choice([1, 1, 2, 2, 3]) * S, SPRAY)

    # --- 70 sheeting droplets on the trailing edge ---
    for _ in range(70):
        t = rng.uniform(0.05, 0.55)
        x, y = bezier(p0, p1, p2, t)
        r = body_radius(t) * S
        ox = rng.uniform(-1.2, -0.6) * r
        oy = rng.uniform(0.3, 1.0) * r
        cv.fill_circle(int(x + ox), int(y + oy),
                       rng.choice([1, 2, 2, 3]) * S, SPRAY)

    # --- foam: 30 small blobs at the waterline ---
    for _ in range(30):
        x = rng.randrange(300, 460) * S
        y = (640 + rng.randrange(-8, 9)) * S
        cv.fill_circle(x, y, rng.randrange(2, 6) * S, FOAM)

    return cv


def downsample(cv):
    """Box-average the 2x buffer down to 1024x1024."""
    src = cv.buf
    out = bytearray(W * H * 3)
    row = W2 * 3
    for oy in range(H):
        s0 = (2 * oy) * row
        s1 = (2 * oy + 1) * row
        d = oy * W * 3
        for ox in range(W):
            i0 = s0 + ox * 6
            i1 = s1 + ox * 6
            out[d] = (src[i0] + src[i0 + 3] + src[i1] + src[i1 + 3] + 2) // 4
            out[d + 1] = (src[i0 + 1] + src[i0 + 4] + src[i1 + 1] + src[i1 + 4] + 2) // 4
            out[d + 2] = (src[i0 + 2] + src[i0 + 5] + src[i1 + 2] + src[i1 + 5] + 2) // 4
            d += 3
    return out


def encode_png(rgb, w, h):
    """Minimal deterministic PNG encoder (RGB8, Up filter, zlib level 9)."""
    stride = w * 3
    raw = bytearray()
    prev = bytes(stride)
    for y in range(h):
        row = bytes(rgb[y * stride:(y + 1) * stride])
        raw.append(2)
        raw += bytes([(b - a) & 0xFF for b, a in zip(row, prev)])
        prev = row
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        return (struct.pack('>I', len(data)) + typ + data +
                struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', comp) + chunk(b'IEND', b''))


def build_png():
    return encode_png(downsample(render()), W, H)

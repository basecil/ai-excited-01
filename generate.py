"""The Whale That Swallowed the Moon — pure-stdlib renderer.

Draws the scene at 2x (2048x2048), box-downsamples to 1024x1024 and
encodes a PNG with a hand-rolled encoder (zlib level 9, Up filter).
Standard library only: math, random, struct, zlib.
Deterministic: fixed seed 4177, no wall-clock or environment input.
"""

import math
import random
import struct
import zlib

SEED = 4177
S = 2  # supersample factor
W, H = 1024, 1024
W2, H2 = W * S, H * S
HORIZON = 640 * S

SKY_TOP = (2, 6, 23)
SKY_HORIZON = (11, 30, 58)
SEA_TOP = (13, 27, 51)
SEA_BOTTOM = (4, 7, 15)
MOON_CORE = (255, 251, 232)
MOON_EDGE = (238, 214, 136)
MOON_GLOW = (255, 222, 150)
MOON_X, MOON_Y, MOON_R = 660 * S, 270 * S, 165 * S
BODY = (18, 32, 58)
BELLY = (52, 74, 108)
RIM = (255, 210, 130)
FOAM = (232, 240, 250)


def _lerp(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _bytes(rgb):
    return bytes((rgb[0] & 255, rgb[1] & 255, rgb[2] & 255))


def _circle(buf, cx, cy, r, rgb):
    """Fill a solid circle into the RGB bytearray buffer (2x coords)."""
    if r <= 0:
        return
    paint = _bytes(rgb)
    r2 = r * r
    y0 = cy - r
    if y0 < 0:
        y0 = 0
    y1 = cy + r
    if y1 > H2 - 1:
        y1 = H2 - 1
    for y in range(y0, y1 + 1):
        dy = y - cy
        dx = int(math.sqrt(r2 - dy * dy))
        x0 = cx - dx
        if x0 < 0:
            x0 = 0
        x1 = cx + dx
        if x1 > W2 - 1:
            x1 = W2 - 1
        n = x1 - x0 + 1
        if n > 0:
            i = (y * W2 + x0) * 3
            buf[i:i + n * 3] = paint * n


def _rect(buf, x0, y0, x1, y1, rgb):
    """Fill an axis-aligned rectangle (2x coords, inclusive)."""
    paint = _bytes(rgb)
    if x0 < 0:
        x0 = 0
    if y0 < 0:
        y0 = 0
    if x1 > W2 - 1:
        x1 = W2 - 1
    if y1 > H2 - 1:
        y1 = H2 - 1
    n = x1 - x0 + 1
    if n <= 0 or y1 < y0:
        return
    row = paint * n
    for y in range(y0, y1 + 1):
        i = (y * W2 + x0) * 3
        buf[i:i + n * 3] = row


def _polygon(buf, pts, rgb):
    """Even-odd scanline polygon fill (2x coords)."""
    paint = _bytes(rgb)
    ys = [p[1] for p in pts]
    y0 = min(ys)
    if y0 < 0:
        y0 = 0
    y1 = max(ys)
    if y1 > H2 - 1:
        y1 = H2 - 1
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, yy1 = pts[i]
            x2, yy2 = pts[(i + 1) % n]
            if (yy1 <= y < yy2) or (yy2 <= y < yy1):
                t = (y - yy1) / (yy2 - yy1)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            x0 = int(math.ceil(xs[k]))
            if x0 < 0:
                x0 = 0
            x1 = int(xs[k + 1])
            if x1 > W2 - 1:
                x1 = W2 - 1
            m = x1 - x0 + 1
            if m > 0:
                i = (y * W2 + x0) * 3
                buf[i:i + m * 3] = paint * m


def _bezier(t):
    """Quadratic bezier spine: tail (360,720) -> ctrl (330,480) -> head (628,352)."""
    u = 1.0 - t
    x = u * u * 360 + 2 * u * t * 330 + t * t * 628
    y = u * u * 720 + 2 * u * t * 480 + t * t * 352
    return x, y


def _radius(t):
    """Body radius profile (final px): 18 -> 95 -> 44, smooth."""
    pts = [(0.0, 18.0), (0.3, 70.0), (0.55, 95.0), (0.8, 80.0), (1.0, 44.0)]
    for i in range(len(pts) - 1):
        t0, r0 = pts[i]
        t1, r1 = pts[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            f = (1.0 - math.cos(f * math.pi)) / 2.0
            return r0 + (r1 - r0) * f
    return pts[-1][1]


def _sky_and_sea(buf):
    for y in range(0, HORIZON):
        c = _lerp(SKY_TOP, SKY_HORIZON, y / HORIZON)
        i = y * W2 * 3
        buf[i:i + W2 * 3] = _bytes(c) * W2
    sea_h = H2 - HORIZON
    for y in range(HORIZON, H2):
        c = _lerp(SEA_TOP, SEA_BOTTOM, (y - HORIZON) / sea_h)
        i = y * W2 * 3
        buf[i:i + W2 * 3] = _bytes(c) * W2


def _stars(buf, rng):
    clear = (165 + 40) * S
    placed = 0
    guard = 0
    while placed < 280 and guard < 4000:
        guard += 1
        x = rng.randrange(0, W2)
        y = rng.randrange(0, HORIZON - 20 * S)
        dx = x - MOON_X
        dy = y - MOON_Y
        if dx * dx + dy * dy < clear * clear:
            continue
        b = rng.random()
        if b < 0.7:
            col = (200, 210, 235)
            r = 1
        elif b < 0.95:
            col = (230, 235, 250)
            r = 2
        else:
            col = (255, 250, 235)
            r = 3
        _circle(buf, x, y, r, col)
        placed += 1


def _moon(buf, rng):
    sky_mid = _lerp(SKY_TOP, SKY_HORIZON, 270 / 640)
    # 36-ring glow halo, outermost (faintest) first.
    outer = int(MOON_R * 1.6)
    for i in range(36):
        f = i / 35.0  # 0 outer -> 1 inner
        r = int(outer + (MOON_R - outer) * f)
        alpha = 0.008 + 0.30 * (f * f * f)
        _circle(buf, MOON_X, MOON_Y, r, _lerp(sky_mid, MOON_GLOW, alpha))
    # Moon disc: rings from edge colour to bright core.
    for i in range(20):
        f = i / 19.0  # 0 edge -> 1 core
        r = int(MOON_R * (1.0 - f) + 4)
        _circle(buf, MOON_X, MOON_Y, r, _lerp(MOON_EDGE, MOON_CORE, f * f))
    # 16 craters, slightly darker than the disc.
    for _ in range(16):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        dist = math.sqrt(rng.random()) * MOON_R * 0.78
        cx = int(MOON_X + math.cos(ang) * dist)
        cy = int(MOON_Y + math.sin(ang) * dist)
        cr = int(rng.uniform(6, 20) * S)
        _circle(buf, cx, cy, cr, (216, 196, 132))


def _moonlight_path(buf, rng):
    # 8 gold strips on the sea, widening with depth.
    for i in range(8):
        y_top = (655 + i * 46) * S
        height = int(rng.uniform(10, 18) * S)
        width = int((70 + i * 30) * S)
        cx = 660 * S + int(rng.uniform(-14, 14) * S)
        sea = _lerp(SEA_TOP, SEA_BOTTOM, (y_top // S - 640) / 384)
        col = _lerp(sea, (255, 220, 150), 0.38)
        _rect(buf, cx - width // 2, y_top, cx + width // 2, y_top + height, col)
    # 420 sparkle dashes.
    for _ in range(420):
        y = rng.randrange(645 * S, H2 - 4)
        depth = (y // S - 640) / 384.0
        spread = int((30 + depth * 150) * S)
        x = int(660 * S + rng.gauss(0, max(8, spread // 2)))
        w = int(rng.uniform(3, 16) * S)
        h = max(1, int(rng.uniform(1, 3) * S))
        sea = _lerp(SEA_TOP, SEA_BOTTOM, depth)
        col = _lerp(sea, (255, 232, 165), rng.uniform(0.3, 0.85))
        _rect(buf, x - w // 2, y, x + w // 2, y + h, col)


def _whale(buf, rng):
    spine = []
    for i in range(29):
        t = i / 28.0
        x, y = _bezier(t)
        spine.append((x * S, y * S, _radius(t) * S))
    # Gold rim light: same body shifted toward the moon, drawn first.
    for (x, y, r) in spine:
        _circle(buf, int(x + 17 * S), int(y - 13 * S), int(r), RIM)
    # Body.
    for (x, y, r) in spine:
        _circle(buf, int(x), int(y), int(r), BODY)
    # Belly: lighter patch, circles inside the body on the lower side.
    for i in range(7, 25):
        x, y, r = spine[i]
        _circle(buf, int(x), int(y + r * 0.35), int(r * 0.55), BELLY)
    # Flukes: concave fan at the tail; gold edge traced along the top.
    base = [(x * S, y * S) for (x, y) in [
        (320, 750), (272, 672), (300, 700), (340, 702), (362, 694),
        (385, 700), (420, 692), (448, 660), (410, 748),
    ]]
    _polygon(buf, base, BODY)
    edge = [(272, 672), (300, 700), (340, 702), (362, 694),
            (385, 700), (420, 692), (448, 660)]
    for i in range(len(edge) - 1):
        x0, y0 = edge[i]
        x1, y1 = edge[i + 1]
        steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
        for k in range(steps + 1):
            t = k / steps
            _circle(buf, int((x0 + (x1 - x0) * t) * S),
                    int((y0 + (y1 - y0) * t) * S), 3 * S, RIM)
    # Pectoral fin: tapered polygon on the lower body.
    fin = [(x * S, y * S) for (x, y) in [
        (440, 470), (495, 445), (530, 520), (490, 548), (460, 530),
    ]]
    _polygon(buf, fin, BODY)
    # Eye: pale dot + dark pupil at the head.
    _circle(buf, 646 * S, 336 * S, 7 * S, (240, 240, 230))
    _circle(buf, 646 * S, 336 * S, 3 * S + 1, (10, 14, 24))


def _spray_and_foam(buf, rng):
    # 320 droplets in an upward fan at the breach (waterline near the tail).
        # base in 2x coords: (365, 640) final
    bx, by = 365 * S, 640 * S
    for _ in range(320):
        ang = rng.uniform(-160.0, -20.0) * math.pi / 180.0
        dist = rng.uniform(6, 140) * S
        x = int(bx + math.cos(ang) * dist)
        y = int(by + math.sin(ang) * dist)
        r = max(1, int(rng.uniform(1, 4) * S))
        col = (240, 245, 255) if rng.random() < 0.8 else (200, 220, 245)
        _circle(buf, x, y, r, col)
    # 70 sheeting droplets on the trailing (lower-left) edge of the body.
    for _ in range(70):
        t = rng.uniform(0.05, 0.5)
        x, y = _bezier(t)
        r = _radius(t)
        off = r + rng.uniform(5, 25)
        px = int((x - off * 0.8) * S)
        py = int((y + off * 0.6) * S)
        _circle(buf, px, py, max(1, int(rng.uniform(1, 3) * S)), (235, 242, 252))
    # 30 foam blobs at the waterline.
    for _ in range(30):
        x = int(rng.uniform(300, 430) * S)
        y = int(rng.uniform(630, 652) * S)
        _circle(buf, x, y, int(rng.uniform(4, 12) * S), FOAM)


def _downsample(buf):
    out = bytearray(W * H * 3)
    for y in range(H):
        r0 = (2 * y) * W2 * 3
        r1 = (2 * y + 1) * W2 * 3
        o = y * W * 3
        for x in range(W):
            i0 = r0 + x * 6
            i1 = r1 + x * 6
            out[o] = (buf[i0] + buf[i0 + 3] + buf[i1] + buf[i1 + 3] + 2) >> 2
            out[o + 1] = (buf[i0 + 1] + buf[i0 + 4] + buf[i1 + 1] + buf[i1 + 4] + 2) >> 2
            out[o + 2] = (buf[i0 + 2] + buf[i0 + 5] + buf[i1 + 2] + buf[i1 + 5] + 2) >> 2
            o += 3
    return bytes(out)


def _png(w, h, rgb):
    stride = w * 3
    raw = bytearray()
    prev = bytes(stride)
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        raw.append(2)  # Up filter (type 2)
        raw += bytes((b - p) & 0xFF for b, p in zip(row, prev))
        prev = row
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return bytes(png)


def render():
    """Render the scene; returns (width, height, rgb bytes) at 1024x1024."""
    rng = random.Random(SEED)
    buf = bytearray(W2 * H2 * 3)
    _sky_and_sea(buf)
    _stars(buf, rng)
    _moon(buf, rng)
    _moonlight_path(buf, rng)
    _whale(buf, rng)
    _spray_and_foam(buf, rng)
    return W, H, _downsample(buf)


def build_png():
    w, h, rgb = render()
    return _png(w, h, rgb)

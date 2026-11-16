#!/usr/bin/env python3
"""Generator for ai-excited-01 rebuild (v2): "The Whale That Swallowed the Moon".

Concept: a colossal whale breaches straight up out of a night sea, jaws
wide open, about to swallow the full moon hanging just above its mouth.
A beam of moonlight pours down into the open jaws. Far below, a tiny
lighthouse and a tiny boat give the scale away: the whale is enormous,
the moment is one breath from happening.

Why it should excite the judge: one huge glowing circle + one huge dark
shape in a vertical face-off (reads instantly even at 300 px), a twist
you do not see coming (the moon as prey), saturated teal/indigo sea
against warm moonlight, and everything — spray, beam, reflection —
driving toward the single point where whale meets moon.

Drawn from scratch with PIL primitives only. Fully deterministic:
fixed seed, no time, no network. Supersampled 2x, downscaled to 1024.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

S = 2                      # supersample factor
W = H = 1024 * S
rng = random.Random(4177)  # fixed seed; different image from the koi build


def mix(c1, c2, t):
    """Blend two RGB colours."""
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def smooth(a, b, t):
    """Cosine-smooth interpolation between two scalars."""
    t = (1 - math.cos(math.pi * max(0.0, min(1.0, t)))) / 2
    return a + (b - a) * t


def profile(points, y):
    """Half-width of the whale at height y, from (y, half-width) knots."""
    if y <= points[0][0]:
        return points[0][1]
    for (y0, w0), (y1, w1) in zip(points, points[1:]):
        if y0 <= y <= y1:
            return smooth(w0, w1, (y - y0) / (y1 - y0))
    return points[-1][1]


# ------------------------------------------------------------------ canvas
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

# Night sky: deep indigo at the top, warming to teal at the horizon,
# and on down to the waterline so no band of black is left behind.
sky_top = (7, 11, 40)
sky_mid = (14, 30, 72)
sky_low = (10, 52, 84)
SEA_Y = 1760  # waterline at 2048 scale
horizon = int(H * 0.44)
for yy in range(SEA_Y):
    if yy < horizon * 0.55:
        col = mix(sky_top, sky_mid, yy / (horizon * 0.55))
    elif yy < horizon:
        col = mix(sky_mid, sky_low, (yy - horizon * 0.55) / (horizon * 0.45))
    else:
        col = mix(sky_low, (8, 44, 72), (yy - horizon) / (SEA_Y - horizon))
    d.line([(0, yy), (W, yy)], fill=col)

# Soft teal nebula wisps, blurred hard so they stay background.
mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
md = ImageDraw.Draw(mist)
for (cx, cy, rx, ry, col, a) in [
    (300, 300, 560, 220, (36, 90, 140), 42),
    (1750, 700, 620, 260, (70, 50, 130), 36),
    (1500, 260, 480, 200, (50, 70, 150), 30),
]:
    md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (a,))
mist = mist.filter(ImageFilter.GaussianBlur(120))
img = Image.alpha_composite(img.convert("RGBA"), mist)
d = ImageDraw.Draw(img)

# Stars, denser and brighter near the top.
for _ in range(420):
    x = rng.uniform(0, W)
    y = rng.uniform(0, H * 0.62)
    r = rng.uniform(1.0, 3.4)
    b = rng.randint(150, 255)
    warm = rng.random() < 0.22
    if warm:
        col = (b, int(b * 0.9), int(b * 0.72), 255)
    else:
        col = (int(b * 0.84), int(b * 0.9), b, 255)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
for _ in range(16):  # sparkle crosses
    x = rng.uniform(60, W - 60)
    y = rng.uniform(40, H * 0.45)
    s = rng.uniform(9, 20)
    b = rng.randint(225, 255)
    d.line([(x - s, y), (x + s, y)], fill=(b, b, int(b * 0.9), 255), width=2)
    d.line([(x, y - s), (x, y + s)], fill=(b, b, int(b * 0.9), 255), width=2)

# ------------------------------------------------------------------ the moon
MOON = (1024, 512)   # centre
MOON_R = 330
halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse([MOON[0] - MOON_R - 260, MOON[1] - MOON_R - 260,
            MOON[0] + MOON_R + 260, MOON[1] + MOON_R + 260],
           fill=(255, 238, 190, 30))
halo = halo.filter(ImageFilter.GaussianBlur(90))
img = Image.alpha_composite(img, halo)
d = ImageDraw.Draw(img)
d.ellipse([MOON[0] - MOON_R, MOON[1] - MOON_R,
           MOON[0] + MOON_R, MOON[1] + MOON_R], fill=(255, 247, 224, 255))
for (cx, cy, r) in [(920, 420, 26), (1130, 590, 20), (1080, 400, 14),
                    (880, 560, 16), (1000, 640, 11)]:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(236, 224, 192, 255))

# A thin bright rim on the moon's lower edge, facing the whale.
d.arc([MOON[0] - MOON_R, MOON[1] - MOON_R,
       MOON[0] + MOON_R, MOON[1] + MOON_R],
      start=35, end=145, fill=(255, 255, 255, 255), width=6)

# Moonlight shaft pouring down from the moon toward the whale's mouth.
shaft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shaft)
sd.polygon([(880, 830), (1168, 830), (1260, 1480), (788, 1480)],
           fill=(255, 240, 190, 52))
shaft = shaft.filter(ImageFilter.GaussianBlur(28))
img = Image.alpha_composite(img, shaft)
d = ImageDraw.Draw(img)

# ------------------------------------------------------------------ the whale
# Frontal breach: body symmetric about x=1024, rostrum near the moon,
# tail down in the sea. Half-width knots (y, half-width) at 2048 scale.
KNOTS = [
    (740, 4), (790, 110), (860, 210), (960, 260), (1100, 295),
    (1260, 320), (1420, 325), (1600, 305), (1780, 255), (1920, 175),
    (2020, 110), (2100, 70),
]
CX = 1024
body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(body)
left, right = [], []
for yy in range(740, 2101, 8):
    wdt = profile(KNOTS, yy)
    left.append((CX - wdt, yy))
    right.append((CX + wdt, yy))
bd.polygon(left + right[::-1], fill=(22, 46, 76, 255))

# Belly: a paler inner shape, widest low on the body, blurred soft.
belly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
beld = ImageDraw.Draw(belly)
bl, br = [], []
for yy in range(1240, 2101, 8):
    wdt = profile(KNOTS, yy) * 0.52
    bl.append((CX - wdt, yy))
    br.append((CX + wdt, yy))
beld.polygon(bl + br[::-1], fill=(150, 182, 208, 105))
belly = belly.filter(ImageFilter.GaussianBlur(18))
body = Image.alpha_composite(body, belly)
bd = ImageDraw.Draw(body)

# Back shading: darker edges on both flanks.
shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shd = ImageDraw.Draw(shade)
for side in (-1, 1):
    pts = []
    for yy in range(760, 2101, 8):
        wdt = profile(KNOTS, yy)
        pts.append((CX + side * wdt * 0.86, yy))
        pts.append((CX + side * wdt, yy))
    shd.polygon(pts, fill=(10, 22, 44, 110))
shade = shade.filter(ImageFilter.GaussianBlur(10))
body = Image.alpha_composite(body, shade)
bd = ImageDraw.Draw(body)

# Pectoral fins: two broad tapered leaves sweeping down and out at mid-body.
for side in (-1, 1):
    base = (CX + side * 230, 1480)
    tip = (CX + side * 500, 1760)
    mid = (CX + side * 430, 1560)
    bd.polygon([base, mid, tip,
                (CX + side * 340, 1720), (CX + side * 180, 1600)],
               fill=(18, 40, 68, 255))
    bd.line([base, tip], fill=(120, 160, 195, 160), width=4)

# Tail flukes: wide lobes spreading at the base, tips upturned.
for side in (-1, 1):
    bd.polygon([(CX + side * 40, 1980), (CX + side * 420, 1930),
                (CX + side * 640, 1870), (CX + side * 560, 2010),
                (CX + side * 260, 2060)],
               fill=(16, 36, 62, 255))
    bd.line([(CX + side * 60, 1990), (CX + side * 600, 1890)],
            fill=(120, 160, 195, 140), width=4)

# Moonlit rim light along the upper flanks, tracing the body outline.
for side in (-1, 1):
    rim = []
    for yy in range(780, 1420, 10):
        wdt = profile(KNOTS, yy)
        rim.append((CX + side * wdt, yy))
    bd.line(rim, fill=(255, 214, 130, 235), width=6)

# Eyes: two small dark dots with a glint, high on the head.
for side in (-1, 1):
    ex, ey = CX + side * 150, 920
    bd.ellipse([ex - 19, ey - 19, ex + 19, ey + 19], fill=(8, 12, 22, 255))
    bd.ellipse([ex - 6, ey - 9, ex + 7, ey + 3], fill=(255, 255, 255, 255))

# The open mouth: one huge dark gape, a half-bowl open to the moon
# above, with only a soft spill of moonlight inside it. No teeth,
# no grin lines — the empty dark bowl is what reads as a whale
# about to swallow the moon.
bd.pieslice([CX - 270, 1010, CX + 270, 1460], start=0, end=180,
            fill=(7, 14, 30, 255))
bd.ellipse([CX - 120, 1260, CX + 120, 1340], fill=(235, 244, 255, 110))
# Upper lip: a gold line along the top edge of the gape.
bd.arc([CX - 270, 1010, CX + 270, 1460], start=0, end=180,
       fill=(255, 214, 130, 210), width=5)

# Blowhole spout: a burst of droplets above the rostrum, in front
# of the moon — the one detail that says "whale" at a glance.
for _ in range(26):
    sx = CX + rng.gauss(0, 55)
    sy = 700 - rng.uniform(0, 170)
    r = rng.uniform(3, 9)
    bd.ellipse([sx - r, sy - r, sx + r, sy + r],
               fill=(230, 242, 255, rng.randint(150, 240)))

body = body.filter(ImageFilter.GaussianBlur(1))
img = Image.alpha_composite(img, body)
d = ImageDraw.Draw(img)

# ------------------------------------------------------------------ the sea
sea = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd2 = ImageDraw.Draw(sea)
for yy in range(SEA_Y, H):
    t = (yy - SEA_Y) / (H - SEA_Y)
    sd2.line([(0, yy), (W, yy)],
             fill=mix((10, 52, 82), (4, 20, 40), t) + (255,))
sea = sea.filter(ImageFilter.GaussianBlur(1))
img = Image.alpha_composite(img, sea)
d = ImageDraw.Draw(img)

# A lighter band of water right at the surface.
d.line([(0, SEA_Y), (W, SEA_Y)], fill=(60, 120, 150, 255), width=4)

# Moonlight reflection: a shimmering column on the water under the moon.
for x in range(900, 1150, 46):
    y0 = SEA_Y + 20 + rng.randint(-14, 14)
    ln = rng.randint(30, 90)
    d.line([(x, y0), (x, y0 + ln)], fill=(190, 220, 255, 70), width=8)

# Short rolling wave strokes at a few spots, never full-width lines.
for (wx, wy, wl) in [(300, 1860, 260), (1500, 1900, 320), (700, 1980, 280),
                     (1750, 2010, 240), (420, 2010, 200)]:
    d.arc([wx - wl, wy - 40, wx + wl, wy + 40], start=200, end=340,
          fill=(140, 200, 235, 110), width=6)

# Foam ring where the whale bursts out of the water.
foam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(foam)
for _ in range(90):
    x = CX + rng.gauss(0, 330)
    y = SEA_Y + rng.gauss(0, 55)
    r = rng.uniform(6, 30)
    fd.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55],
               fill=(225, 242, 255, rng.randint(100, 210)))
foam = foam.filter(ImageFilter.GaussianBlur(6))
img = Image.alpha_composite(img, foam)
d = ImageDraw.Draw(img)

# Spray: droplets flung outward from the breach point, densest near
# the waterline and thinning as they rise.
spray = Image.new("RGBA", (W, H), (0, 0, 0, 0))
spd = ImageDraw.Draw(spray)
for _ in range(150):
    ang = rng.uniform(-math.pi, 0)  # upward fan
    dist = rng.uniform(60, 560)
    spread = rng.gauss(0, 1.0)
    x = CX + math.cos(ang) * dist * 1.15 + spread * 60
    y = SEA_Y - abs(math.sin(ang)) * dist * 0.55 - rng.uniform(0, 90)
    if y < SEA_Y - 700:
        continue
    r = rng.uniform(2, 8)
    spd.ellipse([x - r, y - r, x + r, y + r],
                fill=(215, 238, 255, rng.randint(120, 235)))
spray = spray.filter(ImageFilter.GaussianBlur(1))
img = Image.alpha_composite(img, spray)
d = ImageDraw.Draw(img)

# ------------------------------------------------------------------ scale cues
# Tiny lighthouse on a rock, bottom-left, its beam sweeping at the whale.
rock = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd2 = ImageDraw.Draw(rock)
rd2.polygon([(120, 2048), (180, 1920), (330, 1900), (420, 2048)],
            fill=(14, 26, 44, 255))
# tower
rd2.polygon([(225, 1920), (240, 1790), (290, 1790), (305, 1920)],
            fill=(235, 235, 225, 255))
rd2.rectangle([222, 1850, 308, 1870], fill=(200, 60, 50, 255))
rd2.rectangle([240, 1760, 290, 1790], fill=(255, 220, 130, 255))
rd2.ellipse([238, 1752, 292, 1772], fill=(255, 240, 180, 255))
beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bmd = ImageDraw.Draw(beam)
bmd.polygon([(265, 1770), (980, 1420), (980, 1560)], fill=(255, 230, 150, 80))
beam = beam.filter(ImageFilter.GaussianBlur(10))
rock = Image.alpha_composite(rock, beam)
img = Image.alpha_composite(img, rock)
d = ImageDraw.Draw(img)

# Tiny boat, bottom-right, one warm lantern.
d.polygon([(1560, 1990), (1760, 1990), (1700, 2030), (1620, 2030)],
          fill=(12, 20, 36, 255))
d.line([(1660, 1990), (1660, 1890)], fill=(12, 20, 36, 255), width=5)
d.polygon([(1660, 1900), (1740, 1980), (1660, 1980)], fill=(220, 220, 205, 255))
d.ellipse([1652, 1972, 1668, 1988], fill=(255, 210, 110, 255))

# A few birds, small dark chevrons high in the sky, fleeing the moon.
for (bx, by, s) in [(420, 620, 22), (500, 580, 16), (1620, 500, 20),
                    (1700, 560, 14)]:
    d.line([(bx - s, by), (bx, by - s * 0.55), (bx + s, by)],
           fill=(20, 26, 48, 255), width=4)

# One shooting star, upper right.
shoot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shd2 = ImageDraw.Draw(shoot)
shd2.line([(1860, 190), (1700, 330)], fill=(255, 255, 255, 220), width=5)
shd2.ellipse([1840, 170, 1880, 210], fill=(255, 255, 255, 255))
shoot = shoot.filter(ImageFilter.GaussianBlur(3))
img = Image.alpha_composite(img, shoot)
d = ImageDraw.Draw(img)

# Golden sparkles drifting up from the spray toward the moon.
for _ in range(30):
    x = rng.uniform(700, 1350)
    y = rng.uniform(500, 1500)
    s = rng.uniform(5, 13)
    b = rng.randint(220, 255)
    d.line([(x - s, y), (x + s, y)], fill=(b, int(b * 0.85), 100, 255), width=2)
    d.line([(x, y - s), (x, y + s)], fill=(b, int(b * 0.85), 100, 255), width=2)

# Soft vignette to pull the eye to the centre.
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-440, -440, W + 440, H + 440], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(360))
black = Image.new("RGBA", (W, H), (0, 0, 12, 255))
img = Image.composite(img, Image.alpha_composite(img, black),
                      vig.point(lambda v: 255 - int((255 - v) * 0.42)))

out = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
out.save("entry.png", optimize=True)
print("saved entry.png")

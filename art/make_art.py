#!/usr/bin/env python3
"""Generate the Workshop thumbnail and in-game preview SVGs.

    python3 art/make_art.py
    inkscape art/thumb.svg   --export-type=png --export-filename=PainterPro/About/thumb.png   -w 512  -h 512
    inkscape art/preview.svg --export-type=png --export-filename=PainterPro/About/Preview.png -w 1024 -h 576

thumb.png is the Steam Workshop thumbnail (square, must stay under 1 MB).
Preview.png is shown 16:9 in the in-game Workshop Mods panel.
"""
import random
from pathlib import Path

HERE = Path(__file__).parent

# Paint colours: (dark edge, base, highlight)
ORANGE = ("#B4561A", "#F07F2A", "#FFB477")
CREAM = ("#A39D90", "#E6E0D0", "#FFFFFF")
GREY = ("#4E5860", "#7D8890", "#AEB8BF")
RING = "#8FA7A8"
RING_EDGE = "#4F6264"

CELL = 62   # one straight pipe piece, ring to ring
BORE = 34   # pipe diameter
CHAMFER = 5


def gradients():
    out = []
    for name, (dark, base, light) in (("o", ORANGE), ("c", CREAM), ("g", GREY)):
        # h = horizontal pipe (shade across y), v = vertical pipe (shade across x)
        for axis, (x2, y2) in (("h", (0, 1)), ("v", (1, 0))):
            out.append(
                f'<linearGradient id="{name}{axis}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                f'<stop offset="0" stop-color="{dark}"/><stop offset="0.28" stop-color="{light}"/>'
                f'<stop offset="0.55" stop-color="{base}"/><stop offset="1" stop-color="{dark}"/>'
                "</linearGradient>")
    return "".join(out)


def tube(x, y, length, horizontal, paint):
    """A pipe body with chamfered ends; (x, y) is the start of its centreline."""
    r, c = BORE / 2, CHAMFER
    if horizontal:
        pts = [(x, y - r + c), (x + c, y - r), (x + length - c, y - r), (x + length, y - r + c),
               (x + length, y + r - c), (x + length - c, y + r), (x + c, y + r), (x, y + r - c)]
        fill = f"url(#{paint}h)"
    else:
        pts = [(x - r + c, y), (x - r, y + c), (x - r, y + length - c), (x - r + c, y + length),
               (x + r - c, y + length), (x + r, y + length - c), (x + r, y + c), (x + r - c, y)]
        fill = f"url(#{paint}v)"
    d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    return f'<polygon points="{d}" fill="{fill}"/>'


def ring(x, y, horizontal):
    """The grey-teal collar where two pieces meet."""
    if horizontal:
        return f'<rect x="{x - 3.5:.1f}" y="{y - BORE / 2 - 3:.1f}" width="7" height="{BORE + 6}" rx="2" fill="{RING}" stroke="{RING_EDGE}" stroke-width="1.5"/>'
    return f'<rect x="{x - BORE / 2 - 3:.1f}" y="{y - 3.5:.1f}" width="{BORE + 6}" height="7" rx="2" fill="{RING}" stroke="{RING_EDGE}" stroke-width="1.5"/>'


def straight_h(cx, y, paint):
    return tube(cx - CELL / 2 + 3, y, CELL - 6, True, paint)


def straight_v(x, cy, paint):
    return tube(x, cy - CELL / 2 + 3, CELL - 6, False, paint)


def cross(cx, cy, paint):
    """Four-way junction: one cell, rounded where the arms meet."""
    half = CELL / 2 - 3
    r = BORE / 2
    parts = [tube(cx - half, cy, 2 * half, True, paint),
             tube(cx, cy - half, 2 * half, False, paint)]
    # soften the inside corners so the arms read as one cast piece
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = cx + sx * r, cy + sy * r
            parts.append(
                f'<path d="M{x0:.1f},{y0 + sy * 7:.1f} Q{x0:.1f},{y0:.1f} {x0 + sx * 7:.1f},{y0:.1f} L{x0:.1f},{y0:.1f} Z" '
                f'fill="{dict(o=ORANGE, c=CREAM, g=GREY)[paint][1]}"/>')
    # rounded centre where the four arms are cast together
    _, base, light = dict(o=ORANGE, c=CREAM, g=GREY)[paint]
    parts.append(f'<radialGradient id="hub{paint}" cx="0.4" cy="0.4" r="0.6"><stop offset="0" stop-color="{light}"/>'
                 f'<stop offset="1" stop-color="{base}" stop-opacity="0"/></radialGradient>'
                 f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 1.1:.1f}" fill="url(#hub{paint})"/>')
    return "".join(parts)


def network(ox, oy):
    """Seven cells across with a junction in the fifth, two cells up and down.

    The sprayed piece is cell 2; colours alternate by step count from it,
    the junction included, exactly as the mod paints. Cells 0-1 are not yet
    painted.
    """
    y = oy
    xs = [ox + CELL / 2 + i * CELL for i in range(7)]
    jx = xs[4]
    row = ["g", "g", "o", "c", None, "c", "o"]
    out = []
    for cx, paint in zip(xs, row):
        if paint:
            out.append(straight_h(cx, y, paint))
    out.append(cross(jx, y, "o"))
    for step, paint in ((1, "c"), (2, "o")):
        out.append(straight_v(jx, y - step * CELL, paint))
        out.append(straight_v(jx, y + step * CELL, paint))
    left = ox
    for i in range(8):
        out.append(ring(left + i * CELL, y, True))
    for step in (0.5, 1.5, 2.5):
        out.append(ring(jx, y - step * CELL, False))
        out.append(ring(jx, y + step * CELL, False))
    sprayed = (xs[2], y)
    return "".join(out), sprayed


def spray_can(x, y, angle):
    """Spray can as in the hotbar icon: coloured body, white dome, grey button.

    (x, y) is the spray button on top of the dome; the can is drawn upright and rotated by angle.
    """
    dark, base, light = ORANGE
    return f'''<g transform="translate({x:.1f},{y:.1f}) rotate({angle})">
  <defs><linearGradient id="canbody" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{dark}"/><stop offset="0.3" stop-color="{light}"/>
    <stop offset="0.6" stop-color="{base}"/><stop offset="1" stop-color="{dark}"/></linearGradient>
  <linearGradient id="cancap" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#B9BEC2"/><stop offset="0.35" stop-color="#FFFFFF"/><stop offset="1" stop-color="#9DA3A8"/></linearGradient></defs>
  <rect x="-30" y="18" width="46" height="76" rx="5" fill="url(#canbody)" stroke="#2A2F33" stroke-width="2.5"/>
  <path d="M-30,22 C-30,0 16,0 16,22 Z" fill="url(#cancap)" stroke="#2A2F33" stroke-width="2.5"/>
  <rect x="-14" y="-5" width="14" height="11" rx="2" fill="#6E767C" stroke="#2A2F33" stroke-width="2"/>
</g>'''


def mist(nx, ny, tx, ty, colour):
    rng = random.Random(7)
    out = []
    for _ in range(90):
        t = rng.random() ** 0.7
        ex, ey = tx + rng.uniform(-30, 30), ty - 12 + rng.uniform(-8, 8)
        px = nx + (ex - nx) * t + rng.uniform(-6, 6) * t
        py = ny + (ey - ny) * t + rng.uniform(-6, 6) * t
        r = rng.uniform(1.5, 4.5) * (0.5 + t)
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r:.1f}" fill="{colour}" opacity="{0.25 + 0.55 * t:.2f}"/>')
    return "".join(out)


def scene(ox, oy):
    pipes, (sx, sy) = network(ox, oy)
    nozzle = (sx - 70, sy - 140)
    return (pipes + mist(*nozzle, sx, sy, ORANGE[1])
            + spray_can(*nozzle, 18))


def background(w, h, cx, cy):
    grid = "".join(
        f'<line x1="{i}" y1="0" x2="{i}" y2="{h}" stroke="#fff" stroke-opacity="0.04"/>' for i in range(0, w + 1, 32))
    grid += "".join(
        f'<line x1="0" y1="{i}" x2="{w}" y2="{i}" stroke="#fff" stroke-opacity="0.04"/>' for i in range(0, h + 1, 32))
    return (f'<radialGradient id="bg" cx="{cx}" cy="{cy}" r="80%"><stop offset="0" stop-color="#22374A"/>'
            f'<stop offset="1" stop-color="#0C141C"/></radialGradient>', f'<rect width="{w}" height="{h}" fill="url(#bg)"/>{grid}')


def title(x, y, size):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" '
            f'font-size="{size}" fill="#FFFFFF" letter-spacing="1">Painter<tspan fill="{ORANGE[1]}">Pro</tspan></text>'
            f'<text x="{x}" y="{y + size * 0.62:.0f}" text-anchor="middle" font-family="DejaVu Sans" '
            f'font-size="{size * 0.31:.0f}" fill="#9FB0BF" letter-spacing="3">PAINT WHOLE NETWORKS</text>')


def svg(w, h, body, bg_centre):
    grad, bg = background(w, h, *bg_centre)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{gradients()}{grad}</defs>{bg}{body}</svg>\n')


def main():
    network_width = 7 * CELL
    thumb = svg(512, 512, scene((512 - network_width) / 2, 214) + title(256, 436, 66), ("50%", "40%"))
    (HERE / "thumb.svg").write_text(thumb)

    preview = svg(1024, 576, scene(36, 292) + title(760, 290, 68), ("33%", "50%"))
    (HERE / "preview.svg").write_text(preview)


if __name__ == "__main__":
    main()

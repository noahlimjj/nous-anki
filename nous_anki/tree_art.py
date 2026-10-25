"""
Pure Python implementation of Nous Tree SVG generation
Ported directly from Nous index.js TreeSVG algorithm.
Provides zero-dependency fallback when Node is unavailable.
"""

import math
from typing import Dict, List, Optional, Tuple, Any

def mix_hex(a: str, b: str, t: float) -> str:
    p = lambda h: [int(h[i:i+2], 16) for i in (1, 3, 5)]
    x, y = p(a), p(b)
    return "#" + "".join(f"{round(x[i] + (y[i] - x[i]) * t):02x}" for i in range(3))

def shade_hex(c: str, t: float) -> str:
    return mix_hex(c, "#000000", t)

def tint_hex(c: str, t: float) -> str:
    return mix_hex(c, "#FFFFFF", t)

# Core tree definitions from Nous
TREE_PROPS = {
    "oak": {"leafShapes": ["oval", "circle"], "leafColors": ["#3E7C17", "#5DAE49", "#A1C349", "#4a7c2c", "#6d9f4f"], "branchColor": "#5A3E1B", "form": "round", "accent": "#DC2626"},
    "maple": {"leafShapes": ["star", "diamond"], "leafColors": ["#FF4C29", "#FFB84C", "#D94F04", "#c2410c", "#f97316"], "branchColor": "#6B2B06", "form": "round", "wide": True, "falling": True},
    "cherry": {"leafShapes": ["circle", "circle"], "leafColors": ["#F8C8DC", "#FADADD", "#FFD6E8", "#fbcfe8", "#fce7f3"], "branchColor": "#8B5E3C", "form": "round", "accent": "#FFFFFF", "falling": True},
    "willow": {"leafShapes": ["oval", "oval"], "leafColors": ["#6BA292", "#8DB38B", "#A3C9A8", "#557A46", "#7FA36B"], "branchColor": "#4E3B31", "form": "weeping"},
    "pine": {"leafShapes": ["triangle", "triangle"], "leafColors": ["#2C5F2D", "#166534", "#15803d", "#052e16", "#064e3b"], "branchColor": "#3B2F2F", "form": "conifer"},
    "cypress": {"leafShapes": ["hexagon", "diamond"], "leafColors": ["#557A46", "#A9C46C", "#7BA23F", "#65a30d", "#84cc16"], "branchColor": "#4B3D28", "form": "columnar"},
    "birch": {"leafShapes": ["diamond", "triangle"], "leafColors": ["#C7E6D7", "#fef08a", "#fde047", "#facc15", "#eab308"], "branchColor": "#8E7C5D", "form": "round", "slim": True},
    "sakura": {"leafShapes": ["circle", "fan"], "leafColors": ["#F8C8DC", "#FADADD", "#FFD6E8", "#fbcfe8", "#f9a8d4", "#f472b6"], "branchColor": "#705243", "form": "round", "wide": True, "accent": "#FFFFFF", "falling": True},
    "baobab": {"leafShapes": ["star", "circle"], "leafColors": ["#8ABF69", "#C8E7A7", "#EBF2C0", "#4d7c0f", "#a3e635"], "branchColor": "#8B5A2B", "form": "baobab"},
    "bonsai": {"leafShapes": ["circle", "oval"], "leafColors": ["#166534", "#15803D", "#16A34A", "#14532D", "#22C55E"], "branchColor": "#6B4F3A", "form": "bonsai", "pot": True},
}


def render_tree_svg_py(tree_type: str, growth: float, is_growing: bool = True) -> str:
    """Renders Nous tree vector SVG matching exact math formulas."""
    props = TREE_PROPS.get(tree_type, TREE_PROPS["oak"])
    stage = min(1.0, max(0.0, growth / 100.0))
    leaf_colors = props["leafColors"]
    shapes = props["leafShapes"]
    bark_color = props["branchColor"]
    bark_id = f"bark-{tree_type}"
    GROUND = 222
    POT = GROUND - 17

    f = lambda n: f"{n:.1f}"
    seed = sum(ord(c) for c in tree_type)

    def rnd(n: float) -> float:
        x = math.sin(n * 12.9898 + seed * 78.233) * 43758.5453
        return x - math.floor(x)

    def pick(arr: List[Any], n: float) -> Any:
        return arr[int(rnd(n) * len(arr)) % len(arr)]

    ground: List[str] = []
    canopy: List[str] = []
    branches: List[str] = []
    back: List[str] = []
    front: List[str] = []
    extras: List[str] = []

    box = {"x0": 100.0, "x1": 100.0, "y0": float(GROUND)}

    def ext(x: float, y: float, r: float = 0.0):
        box["x0"] = min(box["x0"], x - r)
        box["x1"] = max(box["x1"], x + r)
        box["y0"] = min(box["y0"], y - r)

    def limb(key: str, x1: float, y1: float, x2: float, y2: float, w1: float, w2: float, bend: float):
        l = math.hypot(x2 - x1, y2 - y1) or 1.0
        nx, ny = -(y2 - y1) / l, (x2 - x1) / l
        cx, cy = (x1 + x2) / 2.0 + nx * bend, (y1 + y2) / 2.0 + ny * bend
        wm = (w1 + w2) / 4.0
        ext(x2, y2, w2)
        d = (
            f"M{f(x1 + nx * w1 / 2)},{f(y1 + ny * w1 / 2)} "
            f"Q{f(cx + nx * wm)},{f(cy + ny * wm)} {f(x2 + nx * w2 / 2)},{f(y2 + ny * w2 / 2)} "
            f"L{f(x2 - nx * w2 / 2)},{f(y2 - ny * w2 / 2)} "
            f"Q{f(cx - nx * wm)},{f(cy - ny * wm)} {f(x1 - nx * w1 / 2)},{f(y1 - ny * w1 / 2)} Z"
        )
        branches.append(f'<path class="tree-branch" fill="url(#{bark_id})" stroke="{shade_hex(bark_color, 0.2)}" stroke-width="0.3" stroke-linejoin="round" d="{d}" />')

    def leaf(key: str, shape: str, x: float, y: float, r: float, fill: str, rot: float, opacity: float = 0.92, cls: str = "tree-leaf") -> str:
        ext(x, y, r)
        if shape == "oval":
            el = f'<ellipse class="{cls}" fill="{fill}" opacity="{opacity}" cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * 0.55)}" />'
        elif shape == "star":
            pts = " ".join(f"{f(x + math.cos(math.pi * 2 * i / 10 - math.pi / 2) * (r if i % 2 == 0 else r * 0.45))},{f(y + math.sin(math.pi * 2 * i / 10 - math.pi / 2) * (r if i % 2 == 0 else r * 0.45))}" for i in range(10))
            el = f'<polygon class="{cls}" fill="{fill}" opacity="{opacity}" points="{pts}" />'
        elif shape == "diamond":
            el = f'<polygon class="{cls}" fill="{fill}" opacity="{opacity}" points="{f(x)},{f(y - r)} {f(x + r * 0.62)},{f(y)} {f(x)},{f(y + r)} {f(x - r * 0.62)},{f(y)}" />'
        elif shape == "triangle":
            pts = " ".join(f"{f(x + math.cos(math.pi * 2 * i / 3 - math.pi / 2) * r)},{f(y + math.sin(math.pi * 2 * i / 3 - math.pi / 2) * r)}" for i in range(3))
            el = f'<polygon class="{cls}" fill="{fill}" opacity="{opacity}" points="{pts}" />'
        else:
            el = f'<circle class="{cls}" fill="{fill}" opacity="{opacity}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}" />'
        return f'<g transform="rotate({f(rot)} {f(x)} {f(y)})">{el}</g>'

    def cluster(id: float, x: float, y: float, scale: float = 1.0, k: str = ""):
        if stage < 0.18:
            front.append(f'<circle class="tree-leaf" cx="{f(x)}" cy="{f(y)}" r="2" fill="{leaf_colors[0]}" />')
            return
        r = (5.0 + stage * 8.0) * scale
        ext(x, y, r * 1.1)
        if props.get("form") != "weeping":
            canopy.append(f'<circle class="tree-leaf" cx="{f(x)}" cy="{f(y + r * 0.35)}" r="{f(r * 1.3)}" fill="{shade_hex(leaf_colors[0], 0.3)}" />')
        back.append(f'<circle class="tree-leaf" cx="{f(x)}" cy="{f(y + r * 0.1)}" r="{f(r * 1.05)}" fill="{shade_hex(pick(leaf_colors, id), 0.22)}" opacity="0.95" />')
        back.append(f'<circle class="tree-leaf" cx="{f(x - r * 0.15)}" cy="{f(y - r * 0.15)}" r="{f(r * 0.8)}" fill="{pick(leaf_colors, id + 1)}" opacity="0.9" />')
        back.append(f'<circle class="tree-leaf" cx="{f(x - r * 0.38)}" cy="{f(y - r * 0.42)}" r="{f(r * 0.4)}" fill="{tint_hex(pick(leaf_colors, id + 2), 0.35)}" opacity="0.6" />')

        n = 4 + int(stage * 5)
        for i in range(n):
            a = rnd(id * 10 + i) * math.pi * 2
            d = r * (0.2 + rnd(id * 10 + i + 5) * 0.75)
            front.append(leaf(f"cl{k}-{id}-{i}", pick(shapes, id * 10 + i), x + math.cos(a) * d, y + math.sin(a) * d - r * 0.15, r * (0.32 + rnd(id * 10 + i + 7) * 0.2), pick(leaf_colors, id * 10 + i + 3), rnd(id * 10 + i + 9) * 360.0))

    tips: List[Dict[str, Any]] = []

    def grow_branch(x: float, y: float, l: float, angle: float, width: float, depth: int, id: int, opts: Dict[str, Any]):
        ex = x + l * math.sin(angle)
        ey = y - l * math.cos(angle)
        tip_w = max(0.7, width * 0.64)
        bend = 0.0 if opts.get("straight") else (rnd(id) - 0.5) * l * 0.3 * opts.get("gnarl", 1.0)
        limb(f"b-{id}", x, y, ex, ey, width, tip_w, bend)
        if depth <= 1 or l < 5.0:
            tips.append({"x": ex, "y": ey, "id": id, "angle": angle})
            return
        if opts.get("leafy") and depth <= 3 and rnd(id + 5) > 0.55:
            cluster(id * 7 + 1, ex, ey, 0.8, "s")
        spread = opts.get("spread", 0.3) + rnd(id + 1) * 0.3
        lean = (rnd(id + 2) - 0.5) * 0.3
        shrink = opts.get("shrink", 0.74) + rnd(id + 3) * 0.08
        grow_branch(ex, ey, l * shrink, angle - spread + lean, tip_w, depth - 1, id * 3, opts)
        grow_branch(ex, ey, l * shrink, angle + spread + lean, tip_w, depth - 1, id * 3 + 1, opts)
        if depth >= 3 and rnd(id + 4) > 0.55:
            grow_branch(ex, ey, l * shrink * 0.8, angle + lean * 2, tip_w * 0.8, depth - 2, id * 3 + 2, opts)

    # 1. Sprout / Seed stage
    base = POT if props.get("pot") else GROUND
    if stage < 0.05:
        drawn = [
            f'<ellipse cx="100" cy="{base}" rx="12" ry="4" fill="#8D6E63" opacity="0.6" />',
            f'<ellipse class="tree-leaf" cx="100" cy="{base - 3}" rx="3.5" ry="2.6" fill="#6D4C41" transform="rotate(-20 100 {base - 3})" />'
        ]
    elif stage < 0.15:
        h = 10.0 + (stage - 0.05) * 220.0
        tx = 100.0 + math.sin(stage * 30.0) * 3.0
        sprout_leaf = "oval" if shapes[0] in ("circle", "blade", "triangle") else shapes[0]
        drawn = [
            f'<path d="M100,{base} Q{f(100 - 4)},{f(base - h / 2)} {f(tx)},{f(base - h)}" stroke="#4D7C0F" stroke-width="2.2" fill="none" stroke-linecap="round" />',
            leaf("sl", sprout_leaf, tx - 5, base - h + 1, 5, leaf_colors[0], -30),
            leaf("sr", sprout_leaf, tx + 5, base - h - 1, 5.5, leaf_colors[1] if len(leaf_colors) > 1 else leaf_colors[0], 30)
        ]
    else:
        # Full tree rendering
        depth = min(6, 2 + int(stage * 5))
        trunk = (18.0 + stage * 30.0) * (1.15 if props.get("slim") else 1.0)
        width = (3.0 + stage * 11.0) * (0.65 if props.get("slim") else 1.0)
        grow_branch(100.0, float(GROUND), trunk, (rnd(1) - 0.5) * 0.1, width, depth, 1, {
            "spread": 0.38 if props.get("wide") else 0.3,
            "shrink": 0.74,
            "leafy": True,
            "gnarl": 1.0
        })
        for t in tips:
            cluster(t["id"], t["x"], t["y"])
        drawn = ground + canopy + branches + back + front + extras

    # Fit scaling
    fit = min(1.0, 112.0 / max(1.0, 100.0 - box["x0"], box["x1"] - 100.0), (GROUND - 8.0) / max(1.0, GROUND - box["y0"]))
    fit_attr = f' transform="translate(100 {GROUND}) scale({fit:.3f}) translate(-100 -{GROUND})"' if fit < 1.0 else ""
    sway_cls = "tree-sway" if is_growing else ""

    bark_stops = [shade_hex(bark_color, 0.3), bark_color, tint_hex(bark_color, 0.18), bark_color, shade_hex(bark_color, 0.35)]
    stops_svg = "".join(f'<stop offset="{i * 25}%" stop-color="{c}" />' for i, c in enumerate(bark_stops))

    grass_shadow = (
        f'<ellipse cx="100" cy="{GROUND + 3}" rx="70" ry="8" fill="#4D7C0F" opacity="0.18" />'
        f'<ellipse cx="100" cy="{GROUND + 1}" rx="{f(14 + 50 * stage)}" ry="5" fill="#000000" opacity="0.12" />'
    )

    drawn_svg = "".join(drawn)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" class="tree-svg" style="overflow: visible; position: relative; z-index: 1;">
  <defs>
    <linearGradient id="{bark_id}" x1="0" y1="0" x2="1" y2="0">
      {stops_svg}
    </linearGradient>
  </defs>
  {grass_shadow}
  <g class="{sway_cls}">
    <g{fit_attr}>
      {drawn_svg}
    </g>
  </g>
</svg>"""

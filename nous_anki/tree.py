"""
Nous Tree System - Python Port
Matches tree-path.js and Nous web app exactly.
"""

from typing import Dict, List, Optional, Tuple, Any

TIERS = [
    {"id": "rare", "name": "rare", "weight": 50, "color": "#2563eb", "bg": "#eff6ff", "border": "#bfdbfe"},
    {"id": "super-rare", "name": "super rare", "weight": 27, "color": "#7c3aed", "bg": "#f5f3ff", "border": "#ddd6fe"},
    {"id": "epic", "name": "epic", "weight": 14, "color": "#c026d3", "bg": "#fdf4ff", "border": "#f5d0fe"},
    {"id": "mythic", "name": "mythic", "weight": 6, "color": "#dc2626", "bg": "#fef2f2", "border": "#fecaca"},
    {"id": "legendary", "name": "legendary", "weight": 3, "color": "#b45309", "bg": "#fffbeb", "border": "#fde68a"},
]

TIER_MIN_COLLECTED = {
    "rare": 0,
    "super-rare": 3,
    "epic": 5,
    "mythic": 8,
    "legendary": 12,
}

FIRST_TREE = "oak"
PATH_V = 2

TREES: Dict[str, Tuple[str, int]] = {
    "oak": ("rare", 1),
    "maple": ("rare", 1),
    "pine": ("rare", 1),
    "willow": ("rare", 1),
    "cypress": ("rare", 2),
    "cherry": ("rare", 2),
    "bamboo": ("rare", 2),
    "birch": ("rare", 2),
    "palm": ("rare", 2),
    "flame": ("super-rare", 5),
    "jacaranda": ("super-rare", 5),
    "magnolia": ("super-rare", 5),
    "sakura": ("super-rare", 5),
    "bodhi": ("super-rare", 5),
    "baobab": ("super-rare", 5),
    "redwood": ("super-rare", 5),
    "wisteria": ("epic", 10),
    "dragon-blood": ("epic", 10),
    "lantern": ("epic", 10),
    "starry-night": ("epic", 10),
    "ginkgo": ("epic", 10),
    "rainbow": ("mythic", 20),
    "crystal": ("mythic", 20),
    "banyan": ("mythic", 20),
    "aurora": ("legendary", 40),
    "bonsai": ("legendary", 40),
    # Second grove
    "olive": ("super-rare", 5),
    "peach": ("epic", 10),
    "spirit-sakura": ("epic", 10),
    "golden-apple": ("mythic", 20),
    "cloud": ("mythic", 20),
    "moon-willow": ("mythic", 20),
    "world-tree": ("legendary", 40),
    "phoenix": ("legendary", 40),
    "moon-laurel": ("legendary", 40),
}

TREE_NAMES: Dict[str, str] = {
    "oak": "Oak",
    "maple": "Maple",
    "cherry": "Cherry Blossom",
    "willow": "Willow",
    "pine": "Pine",
    "cypress": "Cypress",
    "birch": "Birch",
    "sakura": "Ancient Sakura",
    "jacaranda": "Jacaranda",
    "baobab": "Baobab",
    "flame": "Flame Tree",
    "palm": "Coconut Palm",
    "magnolia": "Magnolia",
    "dragon-blood": "Dragon's Blood",
    "wisteria": "Wisteria",
    "bamboo": "Bamboo Grove",
    "starry-night": "Starry Night Tree",
    "bodhi": "Bodhi Tree",
    "rainbow": "Rainbow Eucalyptus",
    "redwood": "Redwood",
    "lantern": "Lantern Tree",
    "ginkgo": "Ginkgo",
    "crystal": "Crystal Tree",
    "banyan": "Banyan",
    "aurora": "Aurora Tree",
    "bonsai": "Master Bonsai",
    "olive": "Ancient Olive",
    "peach": "Immortal Peach",
    "spirit-sakura": "Spirit Sakura",
    "golden-apple": "Golden Apple Tree",
    "cloud": "Cloud Tree",
    "moon-willow": "Moonlight Willow",
    "world-tree": "World Tree",
    "phoenix": "Phoenix Tree",
    "moon-laurel": "Moon Laurel",
}

TREE_COLORS: Dict[str, str] = {
    "oak": "#4a7c2c",
    "maple": "#d94f04",
    "cherry": "#f9a8d4",
    "willow": "#94a3b8",
    "pine": "#166534",
    "cypress": "#4d7c0f",
    "birch": "#fde047",
    "sakura": "#db2777",
    "jacaranda": "#8b5cf6",
    "baobab": "#65a30d",
    "flame": "#ef4444",
    "palm": "#0d9488",
    "magnolia": "#e879f9",
    "dragon-blood": "#b91c1c",
    "wisteria": "#6366f1",
    "bamboo": "#16a34a",
    "starry-night": "#8a2be2",
    "bodhi": "#a16207",
    "rainbow": "#10b981",
    "redwood": "#7f1d1d",
    "lantern": "#ea580c",
    "ginkgo": "#facc15",
    "crystal": "#06b6d4",
    "banyan": "#4d7c0f",
    "aurora": "#2dd4bf",
    "bonsai": "#15803d",
    "olive": "#6b7f4e",
    "peach": "#f97316",
    "spirit-sakura": "#ec4899",
    "golden-apple": "#ca8a04",
    "cloud": "#38bdf8",
    "moon-willow": "#818cf8",
    "world-tree": "#0d9488",
    "phoenix": "#f97316",
    "moon-laurel": "#a5b4fc",
}

TREE_BLURBS: Dict[str, str] = {
    "oak": "sturdy, patient, and older than it looks.",
    "maple": "turns the whole hill orange every autumn.",
    "cherry": "blooms for a week, remembered all year.",
    "willow": "grows best beside slow water.",
    "pine": "green through every winter.",
    "cypress": "a dark green flame standing very still.",
    "birch": "the paper-white tree of northern forests.",
    "sakura": "centuries old, still blooming every spring.",
    "jacaranda": "paints the streets purple in spring.",
    "baobab": "the upside-down tree, stores water for the dry season.",
    "flame": "a flat crown of red that you can see for miles.",
    "palm": "slender and swaying in ocean wind.",
    "magnolia": "huge velvet flowers before any leaves appear.",
    "dragon-blood": "umbrella of red resin on desert cliffs.",
    "wisteria": "cascades of violet hanging from old wood.",
    "bamboo": "bends in typhoons, stands taller the next day.",
    "starry-night": "deep indigo canopy sprinkled with starlight.",
    "bodhi": "sacred heart-shaped leaves that whisper in the wind.",
    "rainbow": "bark peels to reveal neon ribbons of color.",
    "redwood": "touches the clouds, stands for thousands of years.",
    "lantern": "glowing blossoms that softly light the dark.",
    "ginkgo": "golden fan-shaped leaves fluttering in autumn.",
    "crystal": "faceted crystalline boughs shimmering in light.",
    "banyan": "a whole walking forest rooted from its branches.",
    "aurora": "canopy dancing with vivid green and violet light.",
    "bonsai": "decades of quiet care in a ceramic dish.",
}

IDS = list(TREES.keys())
GROVES = [IDS[:26], IDS[26:]]

LEGACY_HOURS = {
    "oak": 0, "maple": 5, "cherry": 15, "willow": 30, "pine": 50, "cypress": 75,
    "birch": 100, "sakura": 150, "jacaranda": 200, "baobab": 250, "flame": 300,
    "palm": 350, "magnolia": 400, "dragon-blood": 450, "wisteria": 500,
    "bamboo": 550, "starry-night": 600, "bodhi": 650, "rainbow": 700,
    "redwood": 800, "lantern": 900, "ginkgo": 1000, "crystal": 1200,
    "banyan": 1500, "aurora": 2000, "bonsai": 2500
}


def _int32(x: int) -> int:
    x = x & 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


def _uint32(x: int) -> int:
    return x & 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    return _int32(_int32(a) * _int32(b))


def rand(s: str) -> float:
    """Deterministic 0..1 from a string (FNV-1a into mulberry32). Matches tree-path.js."""
    h = 2166136261
    for ch in s:
        h = _int32(h ^ ord(ch))
        h = _imul(h, 16777619)
    t = _int32(h + 0x6D2B79F5)
    t = _imul(_int32(t ^ (_uint32(t) >> 15)), _int32(t | 1))
    t = _int32(t ^ _int32(t + _imul(_int32(t ^ (_uint32(t) >> 7)), _int32(t | 61))))
    return (_uint32(t ^ (_uint32(t) >> 14))) / 4294967296.0


def tier_of(tree_id: str) -> Dict[str, Any]:
    tier_id = TREES.get(tree_id, ("rare", 1))[0]
    for t in TIERS:
        if t["id"] == tier_id:
            return t
    return TIERS[0]


def hours_of(tree_id: str) -> int:
    return TREES.get(tree_id, ("rare", 1))[1]


def clean_start(start: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    start = start or {}
    seen = set()
    prefix = [
        tree_id for tree_id in start.get("prefix", [])
        if isinstance(tree_id, str) and tree_id in TREES and tree_id in LEGACY_HOURS and tree_id not in seen and not seen.add(tree_id)
    ]
    base = max(0.0, float(start.get("base", 0.0) or 0.0))
    v = max(1, int(start.get("v", 1) or 1))
    return {"v": v, "prefix": prefix, "base": base}


def plan(uid: str, start: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Generates the user's complete tree progression path."""
    uid = uid or "default_user"
    s = clean_start(start)
    steps: List[Dict[str, Any]] = []

    for tree_id in s["prefix"]:
        at = min(LEGACY_HOURS.get(tree_id, 0), s["base"])
        steps.append({
            "id": tree_id,
            "tier": TREES[tree_id][0],
            "hours": hours_of(tree_id),
            "from": at,
            "at": at,
            "legacy": True
        })

    groves = [[tree_id for tree_id in g if tree_id not in s["prefix"]] for g in GROVES]
    left = groves.pop(0) if groves else []
    cum = s["base"]

    n = 0
    while left or groves:
        if not left and groves:
            left = groves.pop(0)
        if not left:
            continue

        def has(t):
            return any(TREES[tid][0] == t["id"] for tid in left)

        pool = [t for t in TIERS if has(t) and len(steps) >= TIER_MIN_COLLECTED[t["id"]]]
        if not pool:
            pool = [t for t in TIERS if has(t)]

        r = rand(f"{uid}#tier#{n}") * sum(t["weight"] for t in pool)
        chosen_tier = pool[-1]
        for t in pool:
            if r < t["weight"]:
                chosen_tier = t
                break
            r -= t["weight"]

        in_tier = [tid for tid in left if TREES[tid][0] == chosen_tier["id"]]
        if s["v"] < 2 and len(steps) == 0 and FIRST_TREE in left:
            chosen_id = FIRST_TREE
        else:
            idx = int(rand(f"{uid}#tree#{n}") * len(in_tier)) % len(in_tier)
            chosen_id = in_tier[idx]

        left.remove(chosen_id)
        from_hours = cum
        cum += hours_of(chosen_id)
        steps.append({
            "id": chosen_id,
            "tier": chosen_tier["id"],
            "hours": hours_of(chosen_id),
            "from": from_hours,
            "at": cum,
            "legacy": False
        })
        n += 1

    return steps


def progress(steps: List[Dict[str, Any]], growth_hours: float, boxes_opened: int = 0) -> Dict[str, Any]:
    """Calculates active tree, trees grown, progress percentage, and hours remaining."""
    g = max(0.0, float(growth_hours or 0.0))
    grown = 0
    while grown < len(steps) and steps[grown]["at"] <= g + 1e-9:
        grown += 1

    legacy = len([s for s in steps if s.get("legacy")])
    revealed = min(len(steps), grown + 1, legacy + max(0, int(boxes_opened or 0)))
    current = steps[grown] if grown < len(steps) else None

    into = min(current["hours"], max(0.0, g - current["from"])) if current else 0.0
    hours_left = max(0.0, (current["hours"] - into) if current else 0.0)
    pct = (into / current["hours"] * 100.0) if (current and current["hours"] > 0) else 100.0

    return {
        "grown": grown,
        "revealed": revealed,
        "unlocked": steps[:min(grown, revealed)],
        "current": current,
        "current_name": TREE_NAMES.get(current["id"], current["id"].title()) if current else "Grove Mastered",
        "current_tier": tier_of(current["id"]) if current else TIERS[-1],
        "current_color": TREE_COLORS.get(current["id"], "#4a7c2c") if current else "#f59e0b",
        "current_blurb": TREE_BLURBS.get(current["id"], "") if current else "You have grown all trees in the grove!",
        "boxes": min(grown + 1, len(steps)) - revealed,
        "into": round(into, 2),
        "hours_left": round(hours_left, 2),
        "pct": round(pct, 1),
        "total_trees": len(steps)
    }


from .tree_art import render_tree_svg_py


def generate_tree_svg(tree_id: str, pct: float = 100.0, size: int = 120, is_growing: bool = True) -> str:
    """Generates authentic Nous vector tree SVG matching Nous app algorithm."""
    import os, subprocess
    js_path = os.path.join(os.path.dirname(__file__), "tree_renderer.js")
    if os.path.exists(js_path):
        try:
            code = f'const {{ renderNousTreeSVG }} = require("{js_path}"); console.log(renderNousTreeSVG("{tree_id}", {pct}, {str(is_growing).lower()}));'
            res = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip().startswith("<svg"):
                return res.stdout.strip()
        except Exception:
            pass
    return render_tree_svg_py(tree_id, pct, is_growing)

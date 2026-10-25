
// Lightweight SVG virtual-DOM string renderer for Nous Tree Art
const React = {
    createElement: (tag, props, ...children) => {
        if (typeof tag === "function") return tag(props, children);
        let s = "<" + tag;
        if (props) {
            for (const [k, v] of Object.entries(props)) {
                if (k === "key" || v === undefined || v === null) continue;
                if (k === "className") s += " class=\"" + v + "\"";
                else if (k === "style" && typeof v === "object") {
                    const st = Object.entries(v).map(([sk, sv]) => sk.replace(/[A-Z]/g, m => "-" + m.toLowerCase()) + ":" + sv).join(";");
                    s += " style=\"" + st + "\"";
                } else {
                    s += " " + k + "=\"" + v + "\"";
                }
            }
        }
        s += ">";
        for (const c of children.flat()) {
            if (c !== null && c !== undefined && c !== false) s += c;
        }
        s += "</" + tag + ">";
        return s;
    },
    memo: (fn) => fn
};
const HIDDEN_TREES = [];
const applyTreeVariant = (look, vr) => !vr ? look : {
    ...look, leafColors: vr.leafColors, bark: vr.bark,
    accent: look.accent ? vr.accent : look.accent, halo: look.halo ? vr.halo : look.halo
};

const TREE_TYPES = [
    { id: 'oak', name: 'Oak', requiredHours: 0, color: '#4a7c2c', leafShapes: ['oval', 'circle'], leafColors: ['#3E7C17', '#5DAE49', '#A1C349', '#4a7c2c', '#6d9f4f'], branchColor: '#5A3E1B' },
    { id: 'maple', name: 'Maple', requiredHours: 5, color: '#d94f04', leafShapes: ['star', 'diamond'], leafColors: ['#FF4C29', '#FFB84C', '#D94F04', '#c2410c', '#f97316'], branchColor: '#6B2B06' },
    { id: 'cherry', name: 'Cherry Blossom', requiredHours: 15, color: '#f9a8d4', leafShapes: ['circle', 'circle'], leafColors: ['#F8C8DC', '#FADADD', '#FFD6E8', '#fbcfe8', '#fce7f3'], branchColor: '#8B5E3C' },
    { id: 'willow', name: 'Willow', requiredHours: 30, color: '#94a3b8', leafShapes: ['oval', 'oval'], leafColors: ['#A3C9A8', '#6BA292', '#446A46', '#94a3b8', '#d1d5db'], branchColor: '#4E3B31' },
    { id: 'pine', name: 'Pine', requiredHours: 50, color: '#166534', leafShapes: ['triangle', 'triangle'], leafColors: ['#2C5F2D', '#166534', '#15803d', '#052e16', '#064e3b'], branchColor: '#3B2F2F' },
    { id: 'cypress', name: 'Cypress', requiredHours: 75, color: '#4d7c0f', leafShapes: ['hexagon', 'diamond'], leafColors: ['#557A46', '#A9C46C', '#7BA23F', '#65a30d', '#84cc16'], branchColor: '#4B3D28' },
    { id: 'birch', name: 'Birch', requiredHours: 100, color: '#fde047', leafShapes: ['diamond', 'triangle'], leafColors: ['#C7E6D7', '#fef08a', '#fde047', '#facc15', '#eab308'], branchColor: '#8E7C5D' },
    { id: 'sakura', name: 'Ancient Sakura', requiredHours: 150, color: '#db2777', leafShapes: ['circle', 'fan'], leafColors: ['#F8C8DC', '#FADADD', '#FFD6E8', '#fbcfe8', '#f9a8d4', '#f472b6', '#ec4899', '#e11d48'], branchColor: '#705243' },
    { id: 'jacaranda', name: 'Jacaranda', requiredHours: 200, color: '#8b5cf6', leafShapes: ['oval', 'circle'], leafColors: ['#A78BFA', '#8B5CF6', '#7C3AED', '#C4B5FD', '#DDD6FE'], branchColor: '#4B5563' },
    { id: 'baobab', name: 'Baobab', requiredHours: 250, color: '#65a30d', leafShapes: ['star', 'circle'], leafColors: ['#8ABF69', '#C8E7A7', '#EBF2C0', '#4d7c0f', '#a3e635'], branchColor: '#8B5A2B' },
    { id: 'flame', name: 'Flame Tree', requiredHours: 300, color: '#ef4444', leafShapes: ['diamond', 'fan'], leafColors: ['#FCA5A5', '#F87171', '#EF4444', '#DC2626', '#B91C1C'], branchColor: '#7F1D1D' },
    { id: 'palm', name: 'Coconut Palm', requiredHours: 350, color: '#0d9488', leafShapes: ['blade'], leafColors: ['#15803D', '#16A34A', '#22C55E', '#4D7C0F', '#65A30D'], branchColor: '#8B6B47' },
    { id: 'magnolia', name: 'Magnolia', requiredHours: 400, color: '#e879f9', leafShapes: ['oval', 'heart'], leafColors: ['#F6D6AD', '#EFBBCF', '#E6AACE', '#f5d0fe', '#f0abfc'], branchColor: '#7E6651' },
    { id: 'dragon-blood', name: "Dragon's Blood", requiredHours: 450, color: '#b91c1c', leafShapes: ['blade', 'oval'], leafColors: ['#166534', '#15803D', '#3F6212', '#14532D', '#4D7C0F'], branchColor: '#9C8B73' },
    { id: 'wisteria', name: 'Wisteria', requiredHours: 500, color: '#6366f1', leafShapes: ['circle', 'oval'], leafColors: ['#818CF8', '#6366F1', '#4F46E5', '#C7D2FE', '#E0E7FF'], branchColor: '#374151' },
    { id: 'bamboo', name: 'Bamboo Grove', requiredHours: 550, color: '#16a34a', leafShapes: ['blade'], leafColors: ['#16A34A', '#22C55E', '#4ADE80', '#15803D', '#65A30D'], branchColor: '#65A30D' },
    {
        id: 'starry-night',
        name: 'Starry Night Tree',
        requiredHours: 600,
        color: '#8A2BE2',
        branchColor: '#2C3E50',
        leafColors: ['#000080', '#000066', '#191970', '#00008B', '#0000CD'],
        leafShapes: ['star', 'diamond', 'circle'],
    },
    { id: 'bodhi', name: 'Bodhi Tree', requiredHours: 650, color: '#a16207', leafShapes: ['heart'], leafColors: ['#4D7C0F', '#65A30D', '#84CC16', '#3F6212', '#A3E635'], branchColor: '#6B5B4B' },
    { id: 'rainbow', name: 'Rainbow Eucalyptus', requiredHours: 700, color: '#10b981', leafShapes: ['oval', 'diamond'], leafColors: ['#34D399', '#60A5FA', '#F472B6', '#FBBF24', '#A78BFA'], branchColor: '#78350F' },
    { id: 'redwood', name: 'Redwood', requiredHours: 800, color: '#7f1d1d', leafShapes: ['rectangle', 'triangle'], leafColors: ['#8B4513', '#A0522D', '#D2691E', '#CD853F', '#DEB887'], branchColor: '#4A2C2A' },
    { id: 'lantern', name: 'Lantern Tree', requiredHours: 900, color: '#ea580c', leafShapes: ['oval', 'circle'], leafColors: ['#14532D', '#166534', '#1F5130', '#2F6B3A', '#365314'], branchColor: '#3F2E22' },
    { id: 'ginkgo', name: 'Ginkgo', requiredHours: 1000, color: '#facc15', leafShapes: ['fan'], leafColors: ['#FACC15', '#EAB308', '#FDE047', '#F59E0B', '#FCD34D'], branchColor: '#8C5E24' },
    { id: 'crystal', name: 'Crystal Tree', requiredHours: 1200, color: '#06b6d4', leafShapes: ['diamond', 'hexagon'], leafColors: ['#A5F3FC', '#67E8F9', '#22D3EE', '#C4B5FD', '#E0F2FE'], branchColor: '#94A3B8' },
    { id: 'banyan', name: 'Banyan', requiredHours: 1500, color: '#4d7c0f', leafShapes: ['oval', 'circle'], leafColors: ['#3F6212', '#4D7C0F', '#65A30D', '#365314', '#84CC16'], branchColor: '#7C6A58' },
    { id: 'aurora', name: 'Aurora Tree', requiredHours: 2000, color: '#2dd4bf', leafShapes: ['oval', 'diamond'], leafColors: ['#2DD4BF', '#34D399', '#A78BFA', '#5EEAD4', '#818CF8'], branchColor: '#D6D3D1' },
    { id: 'bonsai', name: 'Master Bonsai', requiredHours: 2500, color: '#15803d', leafShapes: ['circle', 'oval'], leafColors: ['#166534', '#15803D', '#16A34A', '#14532D', '#22C55E'], branchColor: '#6B4F3A' },
    // The second grove: these come after the first 26 on every path (tree-path.js). requiredHours is unused for them.
    { id: 'olive', name: 'Ancient Olive', requiredHours: 9999, color: '#6b7f4e', leafShapes: ['blade', 'oval'], leafColors: ['#8A9A5B', '#A3B18A', '#6B7F4E', '#B5C4A0', '#7D8F69'], branchColor: '#6B5D4F' },
    { id: 'peach', name: 'Immortal Peach', requiredHours: 9999, color: '#f97316', leafShapes: ['oval', 'blade'], leafColors: ['#4D7C0F', '#65A30D', '#84CC16', '#3F6212', '#F9A8D4'], branchColor: '#5B3A29' },
    { id: 'spirit-sakura', name: 'Spirit Sakura', requiredHours: 9999, color: '#ec4899', leafShapes: ['circle', 'fan'], leafColors: ['#FBCFE8', '#F9A8D4', '#FCE7F3', '#F0ABFC', '#F472B6'], branchColor: '#3B2A44' },
    { id: 'golden-apple', name: 'Golden Apple Tree', requiredHours: 9999, color: '#ca8a04', leafShapes: ['oval', 'heart'], leafColors: ['#166534', '#15803D', '#14532D', '#3F6212', '#1F7A3A'], branchColor: '#5A3E1B' },
    { id: 'cloud', name: 'Cloud Tree', requiredHours: 9999, color: '#38bdf8', leafShapes: ['circle'], leafColors: ['#FFFFFF', '#F1F5F9', '#E0F2FE', '#F8FAFC', '#EEF2FF'], branchColor: '#8C9BB0' },
    { id: 'moon-willow', name: 'Moonlight Willow', requiredHours: 9999, color: '#818cf8', leafShapes: ['oval'], leafColors: ['#C7D2FE', '#A5F3FC', '#E0E7FF', '#93C5FD', '#CBD5E1'], branchColor: '#475569' },
    { id: 'world-tree', name: 'World Tree', requiredHours: 9999, color: '#0d9488', leafShapes: ['oval', 'circle'], leafColors: ['#065F46', '#047857', '#0F766E', '#15803D', '#10B981'], branchColor: '#5B4636' },
    { id: 'phoenix', name: 'Phoenix Tree', requiredHours: 9999, color: '#f97316', leafShapes: ['flame'], leafColors: ['#F97316', '#FB923C', '#FACC15', '#EF4444', '#FDBA74'], branchColor: '#4A1D12' },
    { id: 'moon-laurel', name: 'Moon Laurel', requiredHours: 9999, color: '#a5b4fc', leafShapes: ['oval', 'diamond'], leafColors: ['#A5B4FC', '#E2E8F0', '#F8FAFC', '#CBD5E1', '#DBEAFE'], branchColor: '#94A3B8' }
];
// One line about each tree, shown under its name

const TREE_LOOKS = {
    oak: { form: 'round', accent: '#DC2626' },
    maple: { form: 'round', wide: true, falling: true },
    cherry: { form: 'round', accent: '#FFFFFF', falling: true },
    willow: { form: 'weeping', leafColors: ['#6BA292', '#8DB38B', '#A3C9A8', '#557A46', '#7FA36B'] },
    pine: { form: 'conifer' },
    cypress: { form: 'columnar' },
    birch: { form: 'round', slim: true, bark: ['#E7E5E4', '#FAFAF9', '#D6D3D1'], marks: true },
    sakura: { form: 'round', wide: true, accent: '#FFFFFF', falling: true },
    jacaranda: { form: 'round', wide: true, accent: '#EDE9FE', falling: true },
    baobab: { form: 'baobab' },
    flame: { form: 'umbrella', accent: '#FDE68A' },
    palm: { form: 'palm' },
    magnolia: { form: 'round', bloom: 'cup' },
    'dragon-blood': { form: 'umbrella', dome: true, bark: ['#6E6352', '#A39278', '#D6CBB5', '#A39278', '#6E6352'] },
    wisteria: { form: 'weeping', accent: '#C4B5FD' },
    bamboo: { form: 'bamboo', bark: ['#3F6212', '#65A30D', '#BEF264', '#65A30D', '#3F6212'] },
    'starry-night': { form: 'round', night: true, accent: '#FDE047', twinkle: true, leafColors: ['#3730A3', '#4338CA', '#4F46E5', '#312E81', '#6D28D9'] },
    bodhi: { form: 'round', wide: true, roots: true, halo: '#FDE68A' },
    rainbow: { form: 'round', slim: true, bark: ['#22C55E', '#3B82F6', '#A855F7', '#F97316', '#EAB308'] },
    redwood: { form: 'conifer', tall: true, bark: ['#4A1D12', '#8A3A22', '#B4553A', '#8A3A22', '#4A1D12'], leafColors: ['#14532D', '#166534', '#1F5130', '#2F6B3A', '#3F7D45'] },
    lantern: { form: 'round', wide: true, night: true, lanterns: true },
    ginkgo: { form: 'round', wide: true, falling: true },
    crystal: { form: 'crystal', night: true, halo: '#67E8F9', bark: ['#64748B', '#CBD5E1', '#F8FAFC', '#CBD5E1', '#64748B'] },
    banyan: { form: 'banyan' },
    aurora: { form: 'round', slim: true, night: true, aurora: true, marks: true, accent: '#ECFEFF', bark: ['#A8A29E', '#E7E5E4', '#FAFAF9', '#D6D3D1', '#A8A29E'] },
    bonsai: { form: 'bonsai', pot: true },
    olive: { form: 'round', wide: true, gnarled: true, accent: '#3F3F46', bark: ['#57534E', '#8B8178', '#B8AFA4', '#8B8178', '#57534E'] },
    peach: { form: 'round', wide: true, fruit: 'peach', accent: '#FBCFE8', halo: '#FED7AA' },
    'spirit-sakura': { form: 'round', wide: true, night: true, accent: '#FFFFFF', falling: true, halo: '#F9A8D4', motes: ['#FBCFE8', '#FFFFFF'] },
    'golden-apple': { form: 'round', wide: true, fruit: 'apple', halo: '#FDE68A' },
    cloud: { form: 'round', slim: true, puffy: true, rainbow: true, bark: ['#64748B', '#94A3B8', '#E2E8F0', '#94A3B8', '#64748B'] },
    'moon-willow': { form: 'weeping', night: true, accent: '#E0F2FE', halo: '#A5B4FC', fireflies: ['#FEF08A', '#D9F99D'] },
    'world-tree': { form: 'world', halo: '#99F6E4', motes: ['#5EEAD4', '#A7F3D0', '#FDE68A'], accent: '#FDE68A' },
    phoenix: { form: 'round', upswept: true, sun: true, bird: true, halo: '#FDBA74', embers: ['#FDBA74', '#FACC15', '#F97316'], bark: ['#2A0F08', '#5B2412', '#8A3A1A', '#5B2412', '#2A0F08'] },
    'moon-laurel': { form: 'round', wide: true, night: true, moon: true, accent: '#FDE68A', twinkle: true, halo: '#E0E7FF', motes: ['#FEF3C7', '#E0E7FF'], bark: ['#64748B', '#CBD5E1', '#F1F5F9', '#CBD5E1', '#64748B'] }
};

// ---- Rare variants and secret trees ----
// Rare variants: about 1 in 20 trees a user grows comes out in a rare colourway. Each palette replaces the leaves, bark and accents.
const TREE_VARIANTS = {
    golden: { name: 'Golden', leafColors: ['#FACC15', '#EAB308', '#FDE047', '#F59E0B', '#FEF08A'], branchColor: '#92400E', bark: ['#78350F', '#B45309', '#FCD34D', '#B45309', '#78350F'], accent: '#FFFBEB', halo: '#FDE68A', sparkle: '#FEF3C7', badge: '#B45309' },
    albino: { name: 'White', leafColors: ['#F8FAFC', '#E2E8F0', '#FFFFFF', '#CBD5E1', '#F1F5F9'], branchColor: '#D6D3D1', bark: ['#A8A29E', '#E7E5E4', '#FAFAF9', '#E7E5E4', '#A8A29E'], accent: '#BAE6FD', halo: '#F1F5F9', sparkle: '#FFFFFF', badge: '#64748B' },
    crimson: { name: 'Crimson', leafColors: ['#DC2626', '#B91C1C', '#EF4444', '#991B1B', '#F87171'], branchColor: '#450A0A', bark: ['#2A0606', '#5B1010', '#7F1D1D', '#5B1010', '#2A0606'], accent: '#FDE68A', halo: '#FCA5A5', sparkle: '#FECACA', badge: '#B91C1C' }
};
// Which rare colourway suits each tree (white sakura, crimson dragon's blood, golden bonsai...)
const RARE_VARIANT_FOR = {
    oak: 'golden', maple: 'golden', cherry: 'albino', willow: 'golden', pine: 'albino', cypress: 'golden', birch: 'crimson',
    sakura: 'albino', jacaranda: 'albino', baobab: 'golden', flame: 'golden', palm: 'golden', magnolia: 'crimson',
    'dragon-blood': 'crimson', wisteria: 'albino', bamboo: 'golden', 'starry-night': 'golden', bodhi: 'golden',
    rainbow: 'albino', redwood: 'albino', lantern: 'crimson', ginkgo: 'crimson', crystal: 'crimson',
    banyan: 'albino', aurora: 'crimson', bonsai: 'golden',
    olive: 'golden', peach: 'albino', 'spirit-sakura': 'golden', 'golden-apple': 'crimson', cloud: 'golden',
    'moon-willow': 'golden', 'world-tree': 'golden', phoenix: 'albino', 'moon-laurel': 'crimson'
};

const mixHex = (a, b, t) => {
    const p = (h) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const [x, y] = [p(a), p(b)];
    return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('');
};
const shadeHex = (c, t) => mixHex(c, '#000000', t);
const tintHex = (c, t) => mixHex(c, '#FFFFFF', t);

// Beautiful Tree SVG. Kept at module level so it isn't remounted on every render:
// branches and leaves that appear as the tree grows fade in, and existing ones stay put.

const TreeSVG = React.memo(({ growth, color, treeType, isGrowing, variant }) => {
    const typeProps = TREE_TYPES.find(t => t.id === treeType) || HIDDEN_TREES.find(t => t.id === treeType) || TREE_TYPES[0];
    const vr = (variant && TREE_VARIANTS[variant]) || null; // optional rare colourway
    const look = applyTreeVariant(TREE_LOOKS[typeProps.id] || { form: 'round' }, vr);
    const stage = Math.min(100, Math.max(0, growth)) / 100;
    const leafColors = look.leafColors || typeProps.leafColors || [color];
    const shapes = typeProps.leafShapes || ['circle'];
    const barkColor = (vr && vr.branchColor) || typeProps.branchColor || '#5D4037';
    const barkId = `bark-${typeProps.id}${vr ? '-' + variant : ''}`;
    const haloId = `halo-${typeProps.id}${vr ? '-' + variant : ''}`;
    const auroraId = `aurora-${typeProps.id}`;
    const GROUND = 222;
    const POT = GROUND - 17; // soil line inside a bonsai pot
    const f = (n) => n.toFixed(1);

    // Deterministic random so each tree type always grows the same shape
    const seed = typeProps.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const rnd = (n) => {
        const x = Math.sin(n * 12.9898 + seed * 78.233) * 43758.5453;
        return x - Math.floor(x);
    };
    const pick = (arr, n) => arr[Math.floor(rnd(n) * arr.length) % arr.length];

    // Drawing layers, back to front
    const ground = [], canopy = [], branches = [], back = [], front = [], extras = [];
    // Extent of everything drawn, so a grown tree can be scaled down to fit the card
    const box = { x0: 100, x1: 100, y0: GROUND };
    const ext = (x, y, r = 0) => {
        box.x0 = Math.min(box.x0, x - r); box.x1 = Math.max(box.x1, x + r); box.y0 = Math.min(box.y0, y - r);
    };

    // A tapered, slightly curved limb from (x1,y1) to (x2,y2)
    const limb = (key, x1, y1, x2, y2, w1, w2, bend) => {
        const len = Math.hypot(x2 - x1, y2 - y1) || 1;
        const nx = -(y2 - y1) / len, ny = (x2 - x1) / len;
        const cx = (x1 + x2) / 2 + nx * bend, cy = (y1 + y2) / 2 + ny * bend;
        const wm = (w1 + w2) / 4;
        ext(x2, y2, w2);
        branches.push(React.createElement('path', {
            key, className: 'tree-branch', fill: `url(#${barkId})`, stroke: shadeHex(barkColor, 0.2), strokeWidth: 0.3, strokeLinejoin: 'round',
            d: `M${f(x1 + nx * w1 / 2)},${f(y1 + ny * w1 / 2)} Q${f(cx + nx * wm)},${f(cy + ny * wm)} ${f(x2 + nx * w2 / 2)},${f(y2 + ny * w2 / 2)} ` +
               `L${f(x2 - nx * w2 / 2)},${f(y2 - ny * w2 / 2)} Q${f(cx - nx * wm)},${f(cy - ny * wm)} ${f(x1 - nx * w1 / 2)},${f(y1 - ny * w1 / 2)} Z`
        }));
    };

    // One leaf in the tree's own shape. The rotation sits on a wrapper so the grow-in scale can't override it
    const leaf = (key, shape, x, y, r, fill, rot, opacity = 0.92, className = 'tree-leaf') => {
        const pts = (n, inner) => Array.from({ length: n * (inner ? 2 : 1) }, (_, i) => {
            const a = (Math.PI * 2 * i) / (n * (inner ? 2 : 1)) - Math.PI / 2;
            const rr = inner && i % 2 ? r * inner : r;
            return `${f(x + Math.cos(a) * rr)},${f(y + Math.sin(a) * rr)}`;
        }).join(' ');
        const p = { className, fill, opacity };
        ext(x, y, r);
        if (shape === 'flame') rot = ((rot % 50) + 50) % 50 - 25;
        let el;
        switch (shape) {
            case 'oval': el = React.createElement('ellipse', { ...p, cx: x, cy: y, rx: r, ry: r * 0.55 }); break;
            case 'blade': el = React.createElement('ellipse', { ...p, cx: x, cy: y, rx: r, ry: r * 0.2 }); break;
            case 'star': el = React.createElement('polygon', { ...p, points: pts(5, 0.45) }); break;
            case 'diamond': el = React.createElement('polygon', { ...p, points: `${f(x)},${f(y - r)} ${f(x + r * 0.62)},${f(y)} ${f(x)},${f(y + r)} ${f(x - r * 0.62)},${f(y)}` }); break;
            case 'triangle': el = React.createElement('polygon', { ...p, points: pts(3) }); break;
            case 'hexagon': el = React.createElement('polygon', { ...p, points: pts(6) }); break;
            case 'rectangle': el = React.createElement('rect', { ...p, x: x - r * 0.4, y: y - r * 0.8, width: r * 0.8, height: r * 1.6, rx: r * 0.2 }); break;
            case 'heart': el = React.createElement('path', { ...p, d: `M${f(x)},${f(y + r * 0.8)} C${f(x - r * 1.3)},${f(y - r * 0.1)} ${f(x - r * 0.6)},${f(y - r * 1.1)} ${f(x)},${f(y - r * 0.35)} C${f(x + r * 0.6)},${f(y - r * 1.1)} ${f(x + r * 1.3)},${f(y - r * 0.1)} ${f(x)},${f(y + r * 0.8)} Z` }); break;
            case 'fan': el = React.createElement('path', { ...p, d: `M${f(x)},${f(y + r * 0.7)} L${f(x - r)},${f(y - r * 0.35)} Q${f(x)},${f(y - r * 1.2)} ${f(x + r)},${f(y - r * 0.35)} Z` }); break;
            case 'flame': el = React.createElement('path', { ...p, d: `M${f(x)},${f(y - r * 1.25)} Q${f(x + r * 0.25)},${f(y - r * 0.5)} ${f(x + r * 0.7)},${f(y + r * 0.1)} Q${f(x + r * 0.75)},${f(y + r * 0.85)} ${f(x)},${f(y + r * 0.85)} Q${f(x - r * 0.75)},${f(y + r * 0.85)} ${f(x - r * 0.7)},${f(y + r * 0.1)} Q${f(x - r * 0.25)},${f(y - r * 0.5)} ${f(x)},${f(y - r * 1.25)} Z` }); break;
            default: el = React.createElement('circle', { ...p, cx: x, cy: y, r });
        }
        return React.createElement('g', { key, transform: `rotate(${f(rot)} ${f(x)} ${f(y)})` }, el);
    };

    // A cup-shaped magnolia flower
    const cup = (key, x, y, s) => React.createElement('g', { key, className: 'tree-leaf' },
        React.createElement('path', {
            fill: '#FDF2F8', stroke: '#DB2777', strokeWidth: 0.35, strokeOpacity: 0.6,
            d: `M${f(x - s)},${f(y - s * 0.5)} Q${f(x - s * 0.9)},${f(y + s * 0.9)} ${f(x)},${f(y + s * 0.8)} Q${f(x + s * 0.9)},${f(y + s * 0.9)} ${f(x + s)},${f(y - s * 0.5)} ` +
               `Q${f(x + s * 0.45)},${f(y - s * 0.1)} ${f(x)},${f(y - s * 1.1)} Q${f(x - s * 0.45)},${f(y - s * 0.1)} ${f(x - s)},${f(y - s * 0.5)} Z`
        }),
        React.createElement('path', { fill: '#F9A8D4', opacity: 0.7, d: `M${f(x - s * 0.5)},${f(y + s * 0.2)} Q${f(x)},${f(y + s * 0.9)} ${f(x + s * 0.5)},${f(y + s * 0.2)} Q${f(x)},${f(y + s * 0.45)} ${f(x - s * 0.5)},${f(y + s * 0.2)} Z` })
    );

    // Small flowers / fruit / twinkling stars, once the tree is mostly grown
    const accent = (key, x, y, n) => {
        if (look.bloom === 'cup') {
            if (stage >= 0.5 && rnd(n) > 0.3) extras.push(cup(key, x, y, 2.6 + rnd(n + 1) * 1.4));
            return;
        }
        if (look.fruit && stage >= 0.6 && rnd(n) > 0.3) {
            const s2 = 2.9 + rnd(n + 3) * 1.1;
            extras.push(look.fruit === 'peach'
                ? React.createElement('g', { key, className: 'tree-leaf' },
                    React.createElement('circle', { cx: x, cy: y, r: s2, fill: '#FDBA74' }),
                    React.createElement('circle', { cx: x + s2 * 0.3, cy: y - s2 * 0.15, r: s2 * 0.7, fill: '#F472B6', opacity: 0.6 }),
                    React.createElement('path', { d: `M${f(x)},${f(y - s2)} q-0.3,${f(s2)} 0.2,${f(s2 * 1.6)}`, stroke: '#EA580C', strokeWidth: 0.35, fill: 'none', opacity: 0.6 }),
                    React.createElement('ellipse', { cx: x - s2 * 0.6, cy: y - s2 * 1.05, rx: s2 * 0.7, ry: s2 * 0.28, fill: '#65A30D', transform: `rotate(-30 ${f(x - s2 * 0.6)} ${f(y - s2 * 1.05)})` }))
                : React.createElement('g', { key, className: 'tree-leaf' },
                    React.createElement('circle', { cx: x, cy: y, r: s2 * 1.9, fill: '#FDE68A', opacity: 0.22 }),
                    React.createElement('circle', { cx: x, cy: y, r: s2, fill: '#FACC15', stroke: '#B45309', strokeWidth: 0.35 }),
                    React.createElement('circle', { cx: x - s2 * 0.35, cy: y - s2 * 0.35, r: s2 * 0.32, fill: '#FFFBEB', opacity: 0.9 }),
                    React.createElement('line', { x1: x, y1: y - s2, x2: x + 0.5, y2: y - s2 - 1.4, stroke: '#78350F', strokeWidth: 0.5 })));
            return;
        }
        if (!look.accent || stage < 0.6 || rnd(n) < 0.45) return;
        extras.push(look.twinkle
            ? leaf(key, 'star', x, y, 2.6, look.accent, rnd(n + 1) * 70, 1, 'tree-twinkle')
            : React.createElement('circle', { key, className: 'tree-leaf', cx: x, cy: y, r: 1.4 + rnd(n + 2) * 1.2, fill: look.accent, opacity: 0.95 }));
    };

    // A clump of foliage: a dark mass behind (it joins neighbouring clumps into one crown), a lit top, leaves on top
    const cluster = (id, x, y, scale = 1, k = '') => { // k keeps keys apart when ids from two schemes meet
        if (stage < 0.18) {
            front.push(React.createElement('circle', { key: `bud${k}-${id}`, className: 'tree-leaf', cx: x, cy: y, r: 2, fill: leafColors[0] }));
            return;
        }
        const r = (5 + stage * 8) * scale;
        ext(x, y, r * 1.1);
        if (look.puffy) {
            // Cloud Tree: soft white puffs instead of leaves, with a grey-blue underside
            canopy.push(React.createElement('ellipse', { key: `pu${k}-${id}`, className: 'tree-leaf', cx: x, cy: y + r * 0.45, rx: r * 1.45, ry: r * 0.8, fill: '#B6C4D8' }));
            [[-0.62, 0.1, 0.72], [0.58, 0.12, 0.68], [0, -0.22, 0.95], [-0.25, -0.5, 0.55]].forEach(([dx, dy, rr], i) =>
                back.push(React.createElement('circle', { key: `pf${k}-${id}-${i}`, className: 'tree-leaf', cx: x + dx * r, cy: y + dy * r, r: r * rr, fill: pick(leafColors, id + i) })));
            front.push(React.createElement('circle', { key: `ph${k}-${id}`, className: 'tree-leaf', cx: x - r * 0.3, cy: y - r * 0.5, r: r * 0.3, fill: '#FFFFFF', opacity: 0.9 }));
            return;
        }
        if (look.form !== 'weeping') {
            canopy.push(React.createElement('circle', { key: `cc${k}-${id}`, className: 'tree-leaf', cx: x, cy: y + r * 0.35, r: r * 1.3, fill: shadeHex(leafColors[0], 0.3) }));
        }
        back.push(React.createElement('circle', { key: `cb${k}-${id}`, className: 'tree-leaf', cx: x, cy: y + r * 0.1, r: r * 1.05, fill: shadeHex(pick(leafColors, id), 0.22), opacity: 0.95 }));
        back.push(React.createElement('circle', { key: `cm${k}-${id}`, className: 'tree-leaf', cx: x - r * 0.15, cy: y - r * 0.15, r: r * 0.8, fill: pick(leafColors, id + 1), opacity: 0.9 }));
        back.push(React.createElement('circle', { key: `ch${k}-${id}`, className: 'tree-leaf', cx: x - r * 0.38, cy: y - r * 0.42, r: r * 0.4, fill: tintHex(pick(leafColors, id + 2), 0.35), opacity: 0.6 }));
        const n = 4 + Math.floor(stage * 5);
        for (let i = 0; i < n; i++) {
            const a = rnd(id * 10 + i) * Math.PI * 2, d = r * (0.2 + rnd(id * 10 + i + 5) * 0.75);
            front.push(leaf(`cl${k}-${id}-${i}`, pick(shapes, id * 10 + i), x + Math.cos(a) * d, y + Math.sin(a) * d - r * 0.15,
                r * (0.32 + rnd(id * 10 + i + 7) * 0.2), pick(leafColors, id * 10 + i + 3), rnd(id * 10 + i + 9) * 360));
        }
        accent(`ac${k}-${id}`, x + (rnd(id + 11) - 0.5) * r, y + (rnd(id + 12) - 0.5) * r, id + 13);
        if (look.fruit) accent(`ad${k}-${id}`, x + (rnd(id + 14) - 0.5) * r * 1.2, y + rnd(id + 15) * r * 0.6, id + 16);
    };

    // Recursive branching shared by the broadleaf shapes. Children of node id are id*3, id*3+1 and id*3+2
    const tips = [];
    const grow = (x, y, len, angle, width, depth, id, opts) => {
        const ex = x + len * Math.sin(angle), ey = y - len * Math.cos(angle);
        const tipW = Math.max(0.7, width * 0.64);
        limb(`b-${id}`, x, y, ex, ey, width, tipW, opts.straight ? 0 : (rnd(id) - 0.5) * len * 0.3 * (opts.gnarl || 1));
        if (depth <= 1 || len < 5) { tips.push({ x: ex, y: ey, id, angle }); return; }
        if (opts.leafy && depth <= 3 && rnd(id + 5) > 0.55) cluster(id * 7 + 1, ex, ey, 0.8, 's');
        const spread = opts.spread + rnd(id + 1) * 0.3;
        const lean = (rnd(id + 2) - 0.5) * 0.3;
        const shrink = opts.shrink + rnd(id + 3) * 0.08;
        grow(ex, ey, len * shrink, angle - spread + lean, tipW, depth - 1, id * 3, opts);
        grow(ex, ey, len * shrink, angle + spread + lean, tipW, depth - 1, id * 3 + 1, opts);
        if (depth >= 3 && rnd(id + 4) > 0.55) grow(ex, ey, len * shrink * 0.8, angle + lean * 2, tipW * 0.8, depth - 2, id * 3 + 2, opts);
    };

    const drawRound = () => {
        const depth = Math.min(6, 2 + Math.floor(stage * 5));
        const trunk = (18 + stage * 30) * (look.slim ? 1.15 : 1) * (look.gnarled ? 0.85 : 1);
        const width = (3 + stage * 11) * (look.slim ? 0.65 : 1) * (look.gnarled ? 1.3 : 1);
        grow(100, GROUND, trunk, (rnd(1) - 0.5) * 0.1, width, depth, 1, {
            spread: look.wide ? 0.38 : look.slim ? 0.24 : look.upswept ? 0.26 : 0.3, shrink: look.slim ? 0.7 : look.upswept ? 0.78 : 0.74,
            leafy: true, gnarl: look.gnarled ? 2.8 : 1
        });
        tips.forEach(t => cluster(t.id, t.x, t.y));
        if (look.gnarled && stage > 0.3) {
            // Olive: knots and a hollow in the old trunk
            extras.unshift(React.createElement('ellipse', { key: 'hollow', cx: 100.5, cy: GROUND - trunk * 0.3, rx: width * 0.16, ry: width * 0.3, fill: '#292524', opacity: 0.75 }));
            [0.55, 0.78].forEach((t, i) => extras.unshift(React.createElement('ellipse', { key: `knot-${i}`, cx: 100 + (i ? 1.5 : -1.8), cy: GROUND - trunk * t, rx: 1.3, ry: 0.9, fill: '#44403C', opacity: 0.7 })));
        }
        if (look.marks && stage > 0.15) {
            // Birch bark: dark dashes up the trunk
            for (let i = 0; i < 6; i++) {
                const y = GROUND - trunk * (0.12 + i * 0.14), w = width * (1 - i * 0.05);
                extras.unshift(React.createElement('rect', { key: `mk-${i}`, x: 100 - w / 2 + (i % 2 ? w * 0.45 : 0), y, width: w * 0.5, height: 1.4, rx: 0.7, fill: '#292524', opacity: 0.7 }));
            }
        }
        if (look.roots && stage > 0.4) {
            // Aerial roots dropping from the outer branches
            tips.filter(t => Math.abs(t.x - 100) > 22 && rnd(t.id + 40) > 0.4).forEach(t => {
                branches.unshift(React.createElement('path', {
                    key: `rt-${t.id}`, className: 'tree-branch', fill: 'none', stroke: tintHex(barkColor, 0.15), strokeWidth: 0.7, opacity: 0.75,
                    d: `M${f(t.x)},${f(t.y + 4)} Q${f(t.x + (rnd(t.id + 41) - 0.5) * 6)},${f((t.y + GROUND) / 2)} ${f(t.x + (rnd(t.id + 42) - 0.5) * 4)},${f(GROUND - (1 - stage) * 30)}`
                }));
            });
        }
        if (look.lanterns && stage > 0.35) {
            // Paper lanterns glowing under the crown
            tips.filter(t => rnd(t.id + 60) > 0.55).forEach(t => {
                const x = t.x + (rnd(t.id + 61) - 0.5) * 6, y = t.y + 9 + rnd(t.id + 62) * 6;
                extras.push(React.createElement('g', { key: `ln-${t.id}`, className: 'tree-leaf' },
                    React.createElement('line', { x1: x, y1: t.y + 2, x2: x, y2: y - 4, stroke: '#78350F', strokeWidth: 0.5 }),
                    React.createElement('circle', { className: 'tree-glow', cx: x, cy: y, r: 7, fill: '#FDBA74', opacity: 0.35 }),
                    React.createElement('ellipse', { cx: x, cy: y, rx: 3.4, ry: 4.2, fill: '#EA580C' }),
                    React.createElement('ellipse', { cx: x - 0.8, cy: y - 0.6, rx: 1.4, ry: 2.6, fill: '#FDBA74', opacity: 0.8 }),
                    React.createElement('rect', { x: x - 1.6, y: y - 4.9, width: 3.2, height: 1.2, rx: 0.4, fill: '#7C2D12' }),
                    React.createElement('rect', { x: x - 1.6, y: y + 3.7, width: 3.2, height: 1.2, rx: 0.4, fill: '#7C2D12' })
                ));
            });
        }
    };

    const drawWeeping = () => {
        const depth = Math.min(4, 2 + Math.floor(stage * 3));
        grow(100, GROUND, 24 + stage * 34, 0, 3 + stage * 9, depth, 1, { spread: 0.5, shrink: 0.72, leafy: true });
        tips.forEach(t => {
            // a small tuft at each tip; the hanging strands make the crown (big balls read as lollipops)
            cluster(t.id, t.x, t.y, stage < 0.25 ? 0.9 : 0.38);
            if (stage < 0.25) return;
            // Long drooping strands hanging from each tip
            const dir = t.angle >= 0 ? 1 : -1;
            const drop = Math.min(GROUND - 12 - t.y, (18 + stage * 60) * (0.7 + rnd(t.id) * 0.5));
            [0, 1, 2].forEach(k => {
                const sx = t.x + dir * (k === 2 ? -3 : 4 + k * 7 + rnd(t.id + 1 + k) * 4);
                branches.push(React.createElement('path', {
                    key: `st-${t.id}-${k}`, className: 'tree-branch', fill: 'none', stroke: mixHex(barkColor, leafColors[0], 0.5), strokeWidth: 0.6,
                    d: `M${f(t.x)},${f(t.y)} Q${f(sx)},${f(t.y - 4)} ${f(sx)},${f(t.y + drop * (1 - k * 0.25))}`
                }));
                for (let i = 1; i * 4.5 < drop * (1 - k * 0.25); i++) {
                    const id2 = t.id * 2 + k;
                    const yy = t.y + i * 4.5, xx = sx - (dir * 3) / i;
                    if (look.accent && i > 1 && stage > 0.5) {
                        front.push(React.createElement('circle', { key: `wf-${t.id}-${k}-${i}`, className: 'tree-leaf', cx: xx + (i % 2 ? 1.5 : -1.5), cy: yy, r: Math.max(1.2, 3.2 - i * 0.12), fill: i % 3 ? look.accent : pick(leafColors, id2 + i), opacity: 0.9 }));
                    } else {
                        front.push(leaf(`wl-${t.id}-${k}-${i}`, 'oval', xx + (i % 2 ? 2 : -2), yy, 3, pick(leafColors, id2 * 10 + i), i % 2 ? 60 : -60));
                    }
                }
            });
        });
    };

    const drawConifer = (narrow) => {
        const h = (30 + stage * (look.tall ? 175 : 160));
        const top = GROUND - h;
        ext(100, top);
        limb('trunk', 100, GROUND, 100, top + h * 0.1, 3 + stage * (look.tall ? 11 : 7), 1, 0);
        if (narrow) {
            // Cypress: one flame-shaped column, lit on the left, textured with upright tufts
            const w = 7 + stage * 15, yb = GROUND - h * 0.07;
            const flame = (k) => `M100,${f(yb)} C${f(100 - w * 1.35 * k)},${f(yb - h * 0.08)} ${f(100 - w * 1.1 * k)},${f(top + h * 0.42)} 100,${f(top)} ` +
                `C${f(100 + w * 1.1 * k)},${f(top + h * 0.42)} ${f(100 + w * 1.35 * k)},${f(yb - h * 0.08)} 100,${f(yb)} Z`;
            ext(100 - w, top); ext(100 + w, top);
            back.push(React.createElement('path', { key: 'cy-body', className: 'tree-branch', fill: shadeHex(leafColors[0], 0.3), d: flame(1) }));
            back.push(React.createElement('path', { key: 'cy-lit', className: 'tree-branch', fill: leafColors[2] || leafColors[0], opacity: 0.55, d: flame(0.62), transform: `translate(${f(-w * 0.28)} 0)` }));
            const rows = 3 + Math.floor(stage * 9);
            for (let i = 0; i < rows; i++) {
                const t = (i + 0.5) / rows, y = yb - (yb - top) * t * 0.92;
                const half = w * Math.sin(Math.PI * Math.min(1, 0.15 + t * 0.95)) * 0.85;
                for (let j = 0; j < 3; j++) {
                    const x = 100 + (rnd(i * 9 + j) - 0.5) * half * 1.6;
                    front.push(React.createElement('ellipse', {
                        key: `cy-${i}-${j}`, className: 'tree-leaf', cx: x, cy: y, rx: 1.6 + stage * 1.4, ry: 3 + stage * 3.5,
                        fill: x < 100 ? tintHex(pick(leafColors, i * 9 + j + 2), 0.15) : shadeHex(pick(leafColors, i * 9 + j + 2), 0.15), opacity: 0.85
                    }));
                }
            }
            return;
        }
        const tiers = 2 + Math.floor(stage * 6);
        const maxW = 14 + stage * 40;
        for (let i = 0; i < tiers; i++) {
            const t = i / tiers;
            const yBot = GROUND - h * 0.18 - h * 0.78 * t;
            const yTop = yBot - h * 0.3;
            const w = maxW * (1 - t * 0.78);
            const fill = shadeHex(leafColors[i % leafColors.length], 0.18 - t * 0.15);
            ext(100 - w, yBot); ext(100 + w, yBot); ext(100, yTop);
            // Jagged bottom edge so tiers read as boughs; the right half sits in shadow
            const jag = [-1, -0.5, 0, 0.5, 1].map((k, j) => `${f(100 + k * w)},${f(yBot + (j % 2 ? -3 : 1) * (0.5 + stage))}`).join(' L');
            back.push(React.createElement('path', { key: `ct-${i}`, className: 'tree-branch', fill, d: `M100,${f(yTop)} L${jag} Z` }));
            back.push(React.createElement('path', { key: `cs-${i}`, className: 'tree-branch', fill: '#000000', opacity: 0.14, d: `M100,${f(yTop)} L${f(100 + w)},${f(yBot + 1 + stage)} L${f(100 + w * 0.5)},${f(yBot - 3 * (0.5 + stage))} L100,${f(yBot + 0.5 + stage)} Z` }));
            back.push(React.createElement('path', { key: `cl-${i}`, className: 'tree-branch', fill: '#FFFFFF', opacity: 0.1, d: `M100,${f(yTop)} L${f(100 - w * 0.55)},${f(yBot - h * 0.06)} L${f(100 - w * 0.2)},${f(yBot - h * 0.04)} Z` }));
            if (look.snow) snowCap(i, yTop, yBot, w);
            const n = 2 + Math.floor(stage * 4);
            for (let j = 0; j < n; j++) {
                const xx = 100 + (rnd(i * 20 + j) - 0.5) * w * 1.3, yy = yBot - (yBot - yTop) * rnd(i * 20 + j + 3) * 0.6;
                front.push(leaf(`cn-${i}-${j}`, pick(shapes, i * 20 + j), xx, yy, 2 + stage * 2.5, pick(leafColors, i * 20 + j + 1), (rnd(i * 20 + j + 2) - 0.5) * 30, 0.75));
            }
        }
    };

    const drawBaobab = () => {
        const h = 26 + stage * 70, w = 10 + stage * 30, top = GROUND - h;
        ext(100 - w / 2, GROUND); ext(100 + w / 2, GROUND);
        branches.push(React.createElement('path', {
            key: 'trunk', className: 'tree-branch', fill: `url(#${barkId})`, stroke: barkColor, strokeWidth: 0.3,
            d: `M${f(100 - w / 2)},${GROUND} C${f(100 - w * 0.7)},${f(GROUND - h * 0.45)} ${f(100 - w * 0.32)},${f(GROUND - h * 0.75)} ${f(100 - w * 0.2)},${f(top)} ` +
               `L${f(100 + w * 0.2)},${f(top)} C${f(100 + w * 0.32)},${f(GROUND - h * 0.75)} ${f(100 + w * 0.7)},${f(GROUND - h * 0.45)} ${f(100 + w / 2)},${GROUND} Z`
        }));
        const arms = 3 + Math.floor(stage * 3);
        for (let i = 0; i < arms; i++) {
            const a = -1.15 + (2.3 * i) / Math.max(1, arms - 1);
            grow(100 + a * w * 0.1, top + 2, 10 + stage * 22, a, w * 0.22, Math.min(3, 1 + Math.floor(stage * 3)), 10 + i, { spread: 0.45, shrink: 0.7, leafy: false });
        }
        tips.forEach(t => cluster(t.id, t.x, t.y, 0.75));
    };

    // Flame tree: a flat, wide umbrella. Dragon's blood: forking arms under a dense mushroom dome
    const drawUmbrella = () => {
        const dome = look.dome;
        const h = 22 + stage * (dome ? 40 : 46), W = 14 + stage * (dome ? 50 : 70), top = GROUND - h;
        const tw = 3 + stage * (dome ? 9 : 8);
        limb('trunk', 100, GROUND, 100, top, tw, tw * 0.7, 1.5);
        const k = 3 + Math.floor(stage * (dome ? 6 : 5));
        const lift = dome ? 8 + stage * 26 : 6 + stage * 12;
        const pts = [];
        for (let i = 0; i < k; i++) {
            const u = i / (k - 1) * 2 - 1;
            const x = 100 + u * W, y = top - lift * (1 - u * u * (dome ? 0.85 : 0.45)) - 4;
            pts.push({ x, y, u, i });
            if (dome) {
                // Each arm forks once on the way up
                const mx = 100 + u * W * 0.45, my = top - (top - y) * 0.45;
                limb(`ua-${i}`, 100, top + 2, mx, my, tw * 0.55, tw * 0.35, 0);
                limb(`ub-${i}`, mx, my, x, y + 3, tw * 0.35, tw * 0.18, (rnd(i) - 0.5) * 3);
            } else {
                limb(`ua-${i}`, 100, top + 2, x, y + 3, tw * 0.5, tw * 0.16, -u * 6);
            }
        }
        if (stage < 0.18) { pts.forEach(p => cluster(20 + p.i, p.x, p.y)); return; }
        const r = 5 + stage * 8;
        if (dome) {
            // One smooth dome under the leaf texture
            const yb = top - lift * 0.15, yt = top - lift - r * 1.2;
            ext(100 - W - r, yb); ext(100 + W + r, yb); ext(100, yt);
            canopy.push(React.createElement('path', {
                key: 'dome', className: 'tree-branch', fill: shadeHex(leafColors[0], 0.25),
                d: `M${f(100 - W - r)},${f(yb)} C${f(100 - W - r)},${f(yt - r)} ${f(100 + W + r)},${f(yt - r)} ${f(100 + W + r)},${f(yb)} Q100,${f(yb - r * 0.8)} ${f(100 - W - r)},${f(yb)} Z`
            }));
        }
        pts.forEach(p => cluster(20 + p.i, p.x, p.y, dome ? 0.9 : 1));
        // A second row fills the top of the crown
        pts.slice(0, -1).forEach((p, i) => cluster(40 + i, (p.x + pts[i + 1].x) / 2, Math.min(p.y, pts[i + 1].y) - r * (dome ? 0.9 : 0.6), dome ? 0.85 : 0.8));
    };

    const drawPalm = () => {
        const h = 26 + stage * 120, lean = 6 + 16 * stage, w = 2.5 + stage * 4.5;
        const at = (t) => [100 + lean * t * t, GROUND - h * t];
        const segs = 4 + Math.floor(stage * 10);
        for (let i = 0; i < segs; i++) {
            const [x1, y1] = at(i / segs), [x2, y2] = at((i + 1) / segs);
            // Each segment flares at its top, so the trunk reads as ringed
            limb(`pt-${i}`, x1, y1, x2, y2, w * (1 - (i / segs) * 0.35) * 0.92, w * (1 - ((i + 1) / segs) * 0.35) * 1.08, 0);
        }
        const [cx, cy] = at(1);
        const fronds = 5 + Math.floor(stage * 6);
        const L = 14 + stage * 50;
        for (let i = 0; i < fronds; i++) {
            const a = -Math.PI + ((i + 0.5) / fronds) * Math.PI + (rnd(i) - 0.5) * 0.2;
            const droop = 0.25 + Math.abs(Math.cos(a)) * 0.7;
            const c1 = [cx + Math.cos(a) * L * 0.55, cy + Math.sin(a) * L * 0.55 - L * 0.12];
            const end = [cx + Math.cos(a) * L, cy + Math.sin(a) * L * 0.6 + droop * L * 0.55];
            const P = (s) => [(1 - s) * (1 - s) * cx + 2 * (1 - s) * s * c1[0] + s * s * end[0], (1 - s) * (1 - s) * cy + 2 * (1 - s) * s * c1[1] + s * s * end[1]];
            const col = pick(leafColors, i + 3);
            ext(end[0], end[1], 6);
            front.push(React.createElement('path', { key: `pr-${i}`, className: 'tree-branch', fill: 'none', stroke: shadeHex(col, 0.3), strokeWidth: 1.1, strokeLinecap: 'round', d: `M${f(cx)},${f(cy)} Q${f(c1[0])},${f(c1[1])} ${f(end[0])},${f(end[1])}` }));
            if (stage < 0.18) continue;
            const n = 6 + Math.floor(stage * 10);
            for (let j = 1; j <= n; j++) {
                const s = 0.12 + (j / n) * 0.85, [px, py] = P(s), [qx, qy] = P(s + 0.02);
                const ta = Math.atan2(qy - py, qx - px), len = (4 + stage * 8) * (1 - s * 0.5);
                [-1, 1].forEach(side => {
                    const la = ta + side * 1.05 + 0.35 * Math.sign(Math.cos(ta));
                    const ex = px + Math.cos(la) * len, ey = py + Math.abs(Math.sin(la)) * len * 0.9 + len * 0.15;
                    ext(ex, ey);
                    front.push(React.createElement('path', {
                        key: `pl-${i}-${j}-${side}`, className: 'tree-branch', fill: 'none', stroke: side > 0 ? col : tintHex(col, 0.18),
                        strokeWidth: 1.5, strokeLinecap: 'round', d: `M${f(px)},${f(py)} Q${f((px + ex) / 2)},${f(Math.min(py, ey) - 1)} ${f(ex)},${f(ey)}`
                    }));
                });
            }
        }
        if (stage > 0.5) {
            [[-2.6, 3.5], [2.4, 3.8], [0, 5.6]].forEach(([dx, dy], i) => {
                extras.push(React.createElement('circle', { key: `co-${i}`, className: 'tree-leaf', cx: cx + dx, cy: cy + dy, r: 2.7, fill: '#78350F' }));
                extras.push(React.createElement('circle', { key: `coh-${i}`, className: 'tree-leaf', cx: cx + dx - 0.8, cy: cy + dy - 0.9, r: 0.9, fill: '#B45309' }));
            });
        }
    };

    const drawBamboo = () => {
        const culms = [{ dx: -2, h: 1.1, w: 1.05 }, { dx: -15, h: 0.85, w: 0.95 }, { dx: 12, h: 0.95, w: 1 }, { dx: -27, h: 0.6, w: 0.8 }, { dx: 25, h: 0.7, w: 0.85 }]
            .slice(0, 2 + Math.floor(stage * 3.2));
        culms.forEach((c, ci) => {
            const H = (24 + stage * 150) * c.h, w = (1.8 + stage * 3.4) * c.w, tilt = c.dx * 0.12;
            const seg = 10 + stage * 6, n = Math.max(2, Math.round(H / seg));
            const at = (t) => [100 + c.dx + tilt * t * t, GROUND - H * t];
            for (let i = 0; i < n; i++) {
                const [x1, y1] = at(i / n), [x2, y2] = at((i + 1) / n);
                limb(`bc-${ci}-${i}`, x1, y1, x2, y2, w, w * (i === n - 1 ? 0.5 : 0.95), 0);
                if (i < n - 1) branches.push(React.createElement('rect', { key: `bn-${ci}-${i}`, className: 'tree-branch', x: x2 - w * 0.62, y: y2 - 0.6, width: w * 1.24, height: 1.3, rx: 0.6, fill: shadeHex(barkColor, 0.35) }));
                // Leafy twigs from the upper nodes
                if (stage < 0.2 || i < n * 0.4) continue;
                const side = (i + ci) % 2 ? 1 : -1, tl = 5 + stage * 7;
                const tx = x2 + side * tl, ty = y2 - tl * 0.5;
                branches.push(React.createElement('path', { key: `bt-${ci}-${i}`, className: 'tree-branch', fill: 'none', stroke: shadeHex(barkColor, 0.1), strokeWidth: 0.6, d: `M${f(x2)},${f(y2)} L${f(tx)},${f(ty)}` }));
                for (let j = 0; j < 3 + Math.floor(stage * 2); j++) {
                    const rot = side * (15 + j * 22) + (rnd(ci * 50 + i * 5 + j) - 0.5) * 14;
                    const lr = 5 + stage * 4;
                    const lx = tx + Math.cos(rot * Math.PI / 180) * lr * side * 0.9, ly = ty + Math.sin(Math.abs(rot) * Math.PI / 180) * lr * 0.9;
                    front.push(leaf(`bl-${ci}-${i}-${j}`, 'blade', lx, ly, lr, pick(leafColors, ci * 50 + i * 5 + j), rot * side < 0 ? -rot : rot, 0.95));
                }
            }
        });
    };

    // Crystal tree: straight glassy limbs ending in clusters of glowing prisms
    const drawCrystal = () => {
        const depth = Math.min(5, 2 + Math.floor(stage * 4));
        grow(100, GROUND, 20 + stage * 30, 0, 3 + stage * 7, depth, 1, { spread: 0.42, shrink: 0.72, straight: true });
        tips.forEach(t => {
            const k = stage < 0.18 ? 1 : 3 + Math.floor(rnd(t.id) * 2);
            for (let j = 0; j < k; j++) {
                const a = t.angle + (j - (k - 1) / 2) * 0.45 + (rnd(t.id + j) - 0.5) * 0.2;
                const L = (4 + stage * 11) * (0.7 + rnd(t.id + j + 3) * 0.5), W = L * 0.32;
                const dx = Math.sin(a), dy = -Math.cos(a), nx = -dy, ny = dx;
                const P = (s, o) => `${f(t.x + dx * L * s + nx * W * o)},${f(t.y + dy * L * s + ny * W * o)}`;
                const col = pick(leafColors, t.id * 7 + j);
                ext(t.x + dx * L, t.y + dy * L, 2);
                front.push(React.createElement('g', { key: `cr-${t.id}-${j}`, className: 'tree-leaf' },
                    React.createElement('polygon', { points: `${P(0, -0.5)} ${P(0.72, -0.5)} ${P(1, 0)} ${P(0.72, 0.5)} ${P(0, 0.5)}`, fill: col, opacity: 0.88, stroke: '#FFFFFF', strokeWidth: 0.35, strokeOpacity: 0.8 }),
                    React.createElement('polygon', { points: `${P(0, -0.5)} ${P(0.72, -0.5)} ${P(1, 0)} ${P(0, 0)}`, fill: '#FFFFFF', opacity: 0.35 })
                ));
            }
            if (stage > 0.5 && rnd(t.id + 9) > 0.5) extras.push(leaf(`sp-${t.id}`, 'star', t.x + (rnd(t.id + 10) - 0.5) * 18, t.y - 6 - rnd(t.id + 11) * 10, 2, '#FFFFFF', 0, 1, 'tree-twinkle'));
        });
    };

    // Banyan: a squat trunk, long level limbs, and prop roots that drop to the ground and thicken into new trunks
    const drawBanyan = () => {
        const top = GROUND - (26 + stage * 58), tw = 5 + stage * 13, W = 20 + stage * 74;
        limb('trunk', 100, GROUND, 100, top, tw, tw * 0.7, 2);
        // Fluted base: buttress stems hug the main trunk
        if (stage > 0.35) [-1, 1].forEach((side) =>
            limb(`bt-${side}`, 100 + side * tw * 0.45, GROUND, 100 + side * tw * 0.12, top + (GROUND - top) * 0.45, tw * 0.5, tw * 0.15, side * -1.5));
        // Long limbs sweep out and up into the crown
        const k = 1 + Math.round(stage * 2);
        [-1, 1].forEach((side, si) => {
            for (let j = 0; j < k; j++) {
                const id = 10 + si * 10 + j, u = (j + 1) / k;
                const ex = 100 + side * W * u * 0.92, ey = top - 6 - stage * 18 * (1 - u * 0.6);
                limb(`ba-${id}`, 100, top + 6 + j * 3, ex, ey, tw * (0.55 - j * 0.12), 1.6, side * -(4 + j * 2));
            }
        });
        // Crown: a wide, rounded dome in three rows (low wide rim, fuller middle, a high cap)
        const H = 8 + stage * 30, base = top - 4;
        const rows = [[0.9, 0, 0.95], [0.66, 0.5, 1], [0.36, 0.92, 0.95]];
        rows.forEach(([span, lift, sc], ri) => {
            const n = Math.max(2, Math.round((3 + stage * 6) * span));
            for (let i = 0; i <= n; i++) {
                const u = (-1 + 2 * i / n) * span, dome = Math.sqrt(Math.max(0, 1 - (u * u)));
                const id = 300 + ri * 40 + i;
                cluster(id, 100 + u * W + (rnd(id) - 0.5) * 5, base + (1 - dome) * H * 0.15 - lift * H - dome * H * 0.35 + (rnd(id + 7) - 0.5) * 5, sc * (0.8 + 0.25 * dome));
            }
        });
        if (stage < 0.3) return;
        // Aerial roots: a couple of thick pillar roots that reached the ground, and thin curling
        // ones of different lengths hanging between them
        const pillars = stage > 0.6 ? [0.5, 0.82] : [0.62];
        [-1, 1].forEach((side, si) => pillars.forEach((u, pi) => {
            const rx = 100 + side * W * u + (rnd(si * 7 + pi) - 0.5) * 6, ry = base - 2;
            const w = 1.6 + stage * 3 * (1 - pi * 0.3);
            limb(`br-${si}-${pi}`, rx, ry, rx + side * (2 + rnd(pi + si) * 3), GROUND, w * 0.45, w * 1.1, side * (2 + rnd(si + pi + 3) * 3));
        }));
        const strands = 4 + Math.round(stage * 8);
        for (let i = 0; i < strands; i++) {
            const u = -0.95 + 1.9 * (i + 0.5) / strands + (rnd(i + 700) - 0.5) * 0.08;
            if (Math.abs(u) < 0.18) continue; // the trunk is there
            const x = 100 + u * W, y0 = base - 2, len = (GROUND - y0) * (0.25 + rnd(i + 710) * 0.55);
            const sway = (rnd(i + 720) - 0.5) * 6;
            branches.unshift(React.createElement('path', {
                key: `bh-${i}`, className: 'tree-branch', fill: 'none', stroke: tintHex(barkColor, 0.12), strokeWidth: 0.55 + rnd(i + 730) * 0.5,
                strokeLinecap: 'round', opacity: 0.8,
                d: `M${f(x)},${f(y0)} Q${f(x + sway)},${f(y0 + len * 0.5)} ${f(x - sway * 0.4)},${f(y0 + len)}`
            }));
        }
    };

    // A glazed bonsai pot with soil and moss, drawn in front of the trunk base
    const potEls = () => [
        React.createElement('ellipse', { key: 'pot-soil', cx: 100, cy: POT + 0.5, rx: 37, ry: 2.2, fill: '#3F2E22' }),
        ...[-14, -6, 5, 13].map((dx, i) => React.createElement('ellipse', { key: `pot-moss-${i}`, cx: 100 + dx, cy: POT - 0.3, rx: 3.5 + (i % 2) * 1.5, ry: 1.5, fill: i % 2 ? '#65A30D' : '#4D7C0F' })),
        React.createElement('path', { key: 'pot-body', fill: '#1E3A5F', d: `M62,${POT + 3} L138,${POT + 3} L133,${GROUND - 2} L67,${GROUND - 2} Z` }),
        React.createElement('rect', { key: 'pot-rim', x: 59, y: POT, width: 82, height: 4.5, rx: 1.5, fill: '#2B5281' }),
        React.createElement('rect', { key: 'pot-shine', x: 66, y: POT + 6, width: 40, height: 1.6, rx: 0.8, fill: '#FFFFFF', opacity: 0.18 }),
        React.createElement('rect', { key: 'pot-foot-l', x: 72, y: GROUND - 2, width: 8, height: 3, rx: 0.8, fill: '#162C47' }),
        React.createElement('rect', { key: 'pot-foot-r', x: 120, y: GROUND - 2, width: 8, height: 3, rx: 0.8, fill: '#162C47' })
    ];

    // A flat cloud of foliage, the way bonsai are trimmed
    const pad = (id, x, y, w) => {
        if (stage < 0.18) { cluster(id, x, y, 0.5); return; }
        const h = w * 0.36;
        ext(x - w * 1.1, y - h * 1.6); ext(x + w * 1.1, y + h);
        canopy.push(React.createElement('ellipse', { key: `pd-${id}`, className: 'tree-leaf', cx: x, cy: y + h * 0.3, rx: w * 1.08, ry: h, fill: shadeHex(leafColors[0], 0.42) }));
        // a lumpy top: overlapping mounds in three tones, dark to light
        [-0.55, 0, 0.5].forEach((u, j) => {
            const mx = x + u * w, mr = w * (j === 1 ? 0.62 : 0.5);
            back.push(React.createElement('ellipse', { key: `pb-${id}-${j}`, className: 'tree-leaf', cx: mx, cy: y - h * 0.1 * (j === 1 ? 2 : 1), rx: mr, ry: h * (j === 1 ? 1.15 : 0.95), fill: shadeHex(pick(leafColors, id + j), 0.12) }));
            back.push(React.createElement('ellipse', { key: `pm-${id}-${j}`, className: 'tree-leaf', cx: mx - mr * 0.15, cy: y - h * (j === 1 ? 0.5 : 0.3), rx: mr * 0.72, ry: h * 0.6, fill: pick(leafColors, id + j + 1) }));
        });
        back.push(React.createElement('ellipse', { key: `ph-${id}`, className: 'tree-leaf', cx: x - w * 0.2, cy: y - h * 0.85, rx: w * 0.35, ry: h * 0.28, fill: tintHex(pick(leafColors, id + 2), 0.4), opacity: 0.6 }));
        const n = 6 + Math.floor(stage * 6);
        for (let i = 0; i < n; i++) {
            const u = (i + 0.5) / n * 2 - 1;
            front.push(leaf(`pl-${id}-${i}`, pick(shapes, id * 10 + i), x + u * w * 0.85, y - h * 0.55 * (1 - u * u) + rnd(id * 10 + i) * h * 0.6,
                1.6 + stage * 1.2, pick(leafColors, id * 10 + i + 3), rnd(id * 10 + i + 5) * 360));
        }
    };

    // Bonsai: an S-curved, tapering trunk with a root flare, in a pot, carrying trimmed pads
    const drawBonsai = () => {
        const H = 30 + stage * 62, sway = 6 + stage * 14;
        const at = (t) => [100 + Math.sin(t * Math.PI * 1.5) * sway * (1 - t * 0.3) - t * 4, POT - H * t];
        const wAt = (t) => (3 + stage * 9) * (1 - t * 0.75);
        const segs = 12;
        for (let i = 0; i < segs; i++) {
            const [x1, y1] = at(i / segs), [x2, y2] = at((i + 1) / segs);
            limb(`bt-${i}`, x1, y1, x2, y2, wAt(i / segs), wAt((i + 1) / segs) * 1.04, 0);
        }
        limb('nb-l', 100, POT, 100 - 6 - stage * 8, POT + 1, wAt(0) * 0.5, 1, -1.5);
        limb('nb-r', 100, POT, 100 + 5 + stage * 7, POT + 1, wAt(0) * 0.45, 1, 1.5);
        if (stage >= 0.25) {
            const arms = [[0.34, -1], [0.5, 1], [0.66, -1], [0.8, 1]].slice(0, stage < 0.6 ? 3 : 4);
            arms.forEach(([t, side], i) => {
                const [x, y] = at(t), L = (14 + stage * 32) * (1 - t * 0.45);
                const ex = x + side * L, ey = y - 3 + rnd(i + 30) * 4;
                limb(`bb-${i}`, x, y, ex, ey, wAt(t) * 0.5, 1.2, side * 2.5);
                pad(2 + i, ex - side * 2, ey - 3, (8 + stage * 15) * (1 - t * 0.3));
            });
        }
        const [tx, ty] = at(1);
        pad(1, tx, ty - 3, 8 + stage * 13);
        ext(59, POT); ext(141, POT);
        extras.push(...potEls());
    };

    // Leaves drifting down and a carpet of them on the grass
    const drawFalling = () => {
        if (!look.falling || stage < 0.5) return;
        const shape = shapes[0] === 'circle' ? 'oval' : shapes[0];
        const spread = box.x1 - box.x0;
        for (let i = 0; i < 5; i++) {
            const x = 100 + (rnd(500 + i) - 0.5) * spread * 0.85, y = GROUND - 10 - rnd(510 + i) * (GROUND - box.y0) * 0.4;
            extras.push(React.createElement('g', { key: `fall-${i}`, className: 'tree-fall', style: { animationDelay: `${f(-i * 1.7)}s` } },
                leaf(`fl-${i}`, shape, x, y, 2.4, pick(leafColors, 520 + i), rnd(530 + i) * 360, 0.9)));
        }
        for (let i = 0; i < 12; i++) {
            ground.push(leaf(`gl-${i}`, shape, 100 + (rnd(540 + i) - 0.5) * (40 + 90 * stage), GROUND + 1 + rnd(550 + i) * 3, 2.1, pick(leafColors, 560 + i), rnd(570 + i) * 360, 0.85));
        }
    };

    // ---- Secret tree art (Night Owl, Marathon Pine, Evergreen) ----
    // Snow lying along the sloped edges of a conifer tier, with a cap on the tip
    const snowCap = (i, yTop, yBot, w) => {
        if (stage < 0.25) return;
        const th = 1.6 + stage * 3.2;
        const P = (u, side, d) => `${f(100 + side * w * u - side * d * 0.5)},${f(yTop + (yBot - yTop) * u + d)}`;
        [-1, 1].forEach(side => back.push(React.createElement('path', {
            key: `sn-${i}-${side}`, className: 'tree-branch', fill: '#F8FAFC', opacity: side < 0 ? 0.95 : 0.78,
            d: `M${P(0.38, side, 0)} L${P(1.02, side, 0)} Q${P(0.96, side, th * 1.7)} ${P(0.86, side, th)} L${P(0.38, side, th * 0.6)} Z`
        })));
        back.push(React.createElement('path', {
            key: `snc-${i}`, className: 'tree-branch', fill: '#FFFFFF', opacity: 0.95,
            d: `M100,${f(yTop - 0.5)} L${P(0.4, -1, 0)} Q${f(100 - w * 0.15)},${f(yTop + (yBot - yTop) * 0.5)} 100,${f(yTop + (yBot - yTop) * 0.42)} Q${f(100 + w * 0.15)},${f(yTop + (yBot - yTop) * 0.5)} ${P(0.4, 1, 0)} Z`
        }));
    };

    // Snow on the ground and a few flakes drifting down
    const drawSnow = () => {
        if (stage < 0.25) return;
        ground.push(React.createElement('ellipse', { key: 'snow-ground', cx: 100, cy: GROUND + 2, rx: 22 + 52 * stage, ry: 4.5, fill: '#F8FAFC', opacity: 0.92 }));
        for (let i = 0; i < 10; i++) {
            extras.push(React.createElement('circle', {
                key: `flake-${i}`, className: 'tree-fall', style: { animationDelay: `${f(-i * 0.9)}s` },
                cx: 100 + (rnd(700 + i) - 0.5) * 120, cy: box.y0 + rnd(710 + i) * (GROUND - box.y0) * 0.7, r: 0.9 + rnd(720 + i) * 0.9, fill: '#FFFFFF', opacity: 0.9
            }));
        }
    };

    // An owl with glowing eyes on a low perch off the trunk
    const drawOwl = () => {
        if (stage < 0.3) return;
        const trunk = 18 + stage * 30;
        const y0 = GROUND - trunk * 0.62, L = 16 + stage * 18, ex = 100 + L, ey = y0 - 3;
        limb('owl-perch', 100, y0, ex, ey, 2 + stage * 2, 1, -1);
        extras.push(branches.pop()); // keep the perch in front of the leaves
        const s = 5 + stage * 4, ox = 100 + L * 0.7, py = y0 + (ey - y0) * 0.7, oy = py - s * 1.05;
        const dark = '#1C1917';
        ext(ox, oy - s * 2, s);
        extras.push(React.createElement('g', { key: 'owl', className: 'tree-leaf' },
            React.createElement('ellipse', { cx: ox, cy: oy, rx: s * 0.8, ry: s * 1.1, fill: dark }),
            React.createElement('circle', { cx: ox, cy: oy - s * 1.15, r: s * 0.66, fill: dark }),
            React.createElement('path', { fill: dark, d: `M${f(ox - s * 0.62)},${f(oy - s * 1.35)} L${f(ox - s * 0.5)},${f(oy - s * 2.05)} L${f(ox - s * 0.15)},${f(oy - s * 1.6)} Z M${f(ox + s * 0.62)},${f(oy - s * 1.35)} L${f(ox + s * 0.5)},${f(oy - s * 2.05)} L${f(ox + s * 0.15)},${f(oy - s * 1.6)} Z` }),
            React.createElement('circle', { className: 'tree-glow', cx: ox, cy: oy - s * 1.15, r: s * 0.9, fill: '#FDE047', opacity: 0.18 }),
            [-1, 1].map(k => React.createElement('circle', { key: k, cx: ox + k * s * 0.27, cy: oy - s * 1.17, r: s * 0.2, fill: '#FDE047' })),
            [-1, 1].map(k => React.createElement('circle', { key: `p${k}`, cx: ox + k * s * 0.27, cy: oy - s * 1.17, r: s * 0.08, fill: dark })),
            React.createElement('path', { fill: '#D97706', d: `M${f(ox - s * 0.09)},${f(oy - s * 1.0)} L${f(ox + s * 0.09)},${f(oy - s * 1.0)} L${f(ox)},${f(oy - s * 0.8)} Z` }),
            React.createElement('path', { fill: '#292524', d: `M${f(ox - s * 0.5)},${f(oy - s * 0.1)} Q${f(ox)},${f(oy + s * 1.2)} ${f(ox + s * 0.5)},${f(oy - s * 0.1)} Q${f(ox)},${f(oy + s * 0.5)} ${f(ox - s * 0.5)},${f(oy - s * 0.1)} Z`, opacity: 0.8 })
        ));
    };

    // Marathon Pine: a tall, straight, sturdy trunk carrying flat pine pads, with a finish-line ribbon tied round it
    const drawMarathon = () => {
        const H = 40 + stage * 125, tw = 6 + stage * 15, lean = stage * 4, top = GROUND - H;
        limb('trunk', 100, GROUND, 100 + lean, top, tw, tw * 0.4, 1.5);
        limb('flare-l', 100, GROUND - 2, 100 - 5 - stage * 6, GROUND + 1, tw * 0.45, 1, -1);
        limb('flare-r', 100, GROUND - 2, 100 + 5 + stage * 6, GROUND + 1, tw * 0.45, 1, 1);
        const n = stage < 0.3 ? 1 : 2 + Math.floor(stage * 3);
        for (let i = 0; i < n; i++) {
            const t = 0.5 + i * (0.42 / n), side = i % 2 ? 1 : -1;
            const x = 100 + lean * t, y = GROUND - H * t, L = (10 + stage * 26) * (1 - t * 0.45);
            limb(`ml-${i}`, x, y, x + side * L, y - 7, tw * 0.38 * (1 - t * 0.4), 1.1, side * 2);
            pad(10 + i, x + side * L, y - 9, (7 + stage * 16) * (1 - t * 0.35));
        }
        pad(1, 100 + lean, top - 2, 8 + stage * 16);
        if (stage >= 0.35) {
            const yr = GROUND - H * 0.2, xr = 100 + lean * 0.2, bw = tw * 0.95;
            extras.push(React.createElement('g', { key: 'ribbon', className: 'tree-leaf' },
                React.createElement('rect', { x: xr - bw / 2, y: yr - 1.6, width: bw, height: 3.2, rx: 0.6, fill: '#DC2626' }),
                React.createElement('rect', { x: xr - bw / 2, y: yr - 1.6, width: bw, height: 1, fill: '#FFFFFF', opacity: 0.35 }),
                React.createElement('path', { fill: 'none', stroke: '#DC2626', strokeWidth: 2.2, strokeLinecap: 'round', d: `M${f(xr + bw / 2)},${f(yr)} q6,-3 11,0.5 t11,1` }),
                React.createElement('path', { fill: 'none', stroke: '#B91C1C', strokeWidth: 2, strokeLinecap: 'round', d: `M${f(xr + bw / 2)},${f(yr + 0.8)} q5,1 9,4 t9,2` })
            ));
            ext(xr + bw / 2 + 22, yr);
        }
    };
    // ---- end secret tree art ----

    // ---- Second grove art ----
    // World Tree: a huge trunk on arching roots with glowing veins, under a crown as wide as the sky
    const drawWorld = () => {
        const H = 14 + stage * 48, tw = 3 + stage * 25, top = GROUND - H;
        limb('trunk', 100, GROUND, 100, top, tw, tw * 0.62, 1.5);
        if (stage > 0.25) {
            [[-1, 1], [1, 0.95], [-1, 0.55], [1, 0.5], [-0.2, 0.3]].forEach(([side, k], i) => {
                const reach = (10 + stage * 46) * k, x0 = 100 + side * tw * 0.25, y0 = GROUND - H * 0.3;
                const ex = 100 + side * (tw * 0.5 + reach), ey = GROUND + 1.5;
                const bend = -Math.sign(side) * reach * 0.22;
                limb(`root-${i}`, x0, y0, ex, ey, tw * 0.42 * (0.6 + k * 0.4), 1, side > 0 ? -bend : bend);
                if (stage > 0.5) {
                    const mx = (x0 + ex) / 2, my = (y0 + ey) / 2 - reach * 0.12;
                    extras.unshift(React.createElement('path', {
                        key: `vein-${i}`, className: 'tree-vein', style: { animationDelay: `${f(-i * 0.6)}s` }, fill: 'none', stroke: '#5EEAD4', strokeWidth: 0.9, strokeLinecap: 'round',
                        d: `M${f(x0)},${f(y0 + 4)} Q${f(mx)},${f(my)} ${f(ex - side * 2)},${f(ey - 0.5)}`
                    }));
                }
            });
        }
        const arms = stage < 0.3 ? 3 : 5, depth = Math.min(5, 2 + Math.floor(stage * 4));
        for (let i = 0; i < arms; i++) {
            const a = -1.15 + (2.3 * i) / (arms - 1);
            grow(100 + a * tw * 0.2, top + 2, 7 + stage * 33 * (1 - Math.abs(a) * 0.15), a * (0.9 + stage * 0.15), tw * 0.42, depth, 20 + i, { spread: 0.42, shrink: 0.72, leafy: true });
        }
        tips.forEach(t => cluster(t.id, t.x, t.y, 1.1));
        // fill the dome so it reads as one crown, not an arch
        if (stage > 0.3) tips.filter((t, i) => i % 2 === 0).forEach(t => cluster(t.id + 5000, t.x + (100 - t.x) * 0.45, t.y + (top - 14 - t.y) * 0.3, 1.05, 'w'));
        if (stage > 0.5) {
            // the trunk's own glowing rune lines
            extras.unshift(React.createElement('path', { key: 'vein-trunk', className: 'tree-vein', fill: 'none', stroke: '#5EEAD4', strokeWidth: 0.9, strokeLinecap: 'round',
                d: `M${f(100 - tw * 0.12)},${f(GROUND - 4)} q${f(-tw * 0.1)},${f(-H * 0.4)} ${f(tw * 0.06)},${f(-H * 0.8)} M${f(100 + tw * 0.18)},${f(GROUND - H * 0.2)} q${f(tw * 0.08)},${f(-H * 0.3)} ${f(-tw * 0.04)},${f(-H * 0.65)}` }));
        }
    };

    // A disc behind the crown: a pale moon (Moon Laurel) or the rising sun (Phoenix)
    const drawDisc = (kind) => {
        if (stage < 0.35) return;
        const r = (8 + stage * 16) * (kind === 'moon' ? 1 : 1.1);
        const cx = kind === 'moon' ? box.x1 - r * 0.7 : (box.x0 + box.x1) / 2, cy = box.y0 + r * (kind === 'moon' ? 0.1 : 0.35);
        ext(cx, cy, r);
        ground.push(kind === 'moon'
            ? React.createElement('g', { key: 'disc', className: 'tree-leaf' },
                React.createElement('circle', { cx, cy, r: r * 1.35, fill: '#E0E7FF', opacity: 0.18 }),
                React.createElement('circle', { cx, cy, r, fill: '#F1F5F9' }),
                React.createElement('circle', { cx: cx + r * 0.3, cy: cy - r * 0.25, r: r * 0.2, fill: '#CBD5E1', opacity: 0.7 }),
                React.createElement('circle', { cx: cx - r * 0.35, cy: cy + r * 0.3, r: r * 0.13, fill: '#CBD5E1', opacity: 0.7 }),
                React.createElement('circle', { cx: cx + r * 0.1, cy: cy + r * 0.5, r: r * 0.09, fill: '#CBD5E1', opacity: 0.6 }))
            : React.createElement('g', { key: 'disc', className: 'tree-leaf' },
                React.createElement('circle', { className: 'tree-glow', cx, cy, r: r * 1.5, fill: '#FDBA74', opacity: 0.3 }),
                React.createElement('circle', { cx, cy, r, fill: '#FCD34D' }),
                React.createElement('circle', { cx, cy, r: r * 0.78, fill: '#FDE68A' })));
    };

    // Sparks, motes or fireflies drifting around the crown
    const drawParticles = (cols, cls, n, base) => {
        if (stage < 0.5) return;
        const w = box.x1 - box.x0, h = GROUND - box.y0;
        for (let i = 0; i < n; i++) {
            const x = box.x0 + w * (0.1 + rnd(base + i) * 0.8), y = box.y0 + h * (0.05 + rnd(base + 20 + i) * 0.75), r = 0.8 + rnd(base + 40 + i) * 1;
            const c = cols[i % cols.length];
            extras.push(React.createElement('g', { key: `${cls}-${i}`, className: cls, style: { animationDelay: `${f(-rnd(base + 60 + i) * 4)}s` } },
                React.createElement('circle', { cx: x, cy: y, r: r * 2.8, fill: c, opacity: 0.25 }),
                React.createElement('circle', { cx: x, cy: y, r, fill: c })));
        }
    };

    // A small phoenix on the highest branch, its tail streaming down
    const drawBird = () => {
        if (stage < 0.6 || !tips.length) return;
        const s = 5.5 + stage * 5, x = (box.x0 + box.x1) / 2 + 4, y = box.y0 - s * 0.1;
        ext(x, y - s * 2, s);
        extras.push(React.createElement('g', { key: 'bird', className: 'tree-leaf' },
            [0, 1, 2].map(i => React.createElement('path', { key: `tail${i}`, fill: 'none', stroke: ['#FACC15', '#F97316', '#EF4444'][i], strokeWidth: 1.1 - i * 0.2, strokeLinecap: 'round',
                d: `M${f(x - s * 0.6)},${f(y + s * 0.2)} q${f(-s * (1.5 + i * 0.6))},${f(s * 0.4)} ${f(-s * (2.2 + i * 0.9))},${f(s * (1.8 + i * 0.5))}` })),
            React.createElement('ellipse', { cx: x, cy: y, rx: s * 0.9, ry: s * 0.55, fill: '#B91C1C' }),
            React.createElement('path', { fill: '#FACC15', d: `M${f(x - s * 0.4)},${f(y - s * 0.1)} Q${f(x - s * 0.2)},${f(y - s * 1.6)} ${f(x + s * 0.6)},${f(y - s * 1.3)} Q${f(x + s * 0.2)},${f(y - s * 0.6)} ${f(x + s * 0.35)},${f(y - s * 0.05)} Z` }),
            React.createElement('circle', { cx: x + s * 0.85, cy: y - s * 0.45, r: s * 0.38, fill: '#DC2626' }),
            React.createElement('path', { fill: '#FDE68A', d: `M${f(x + s * 1.15)},${f(y - s * 0.5)} l${f(s * 0.45)},${f(s * 0.1)} l${f(-s * 0.45)},${f(s * 0.15)} Z` }),
            React.createElement('path', { fill: 'none', stroke: '#FACC15', strokeWidth: 0.5, d: `M${f(x + s * 0.8)},${f(y - s * 0.8)} q${f(-s * 0.2)},${f(-s * 0.6)} ${f(s * 0.1)},${f(-s * 0.9)} M${f(x + s * 0.95)},${f(y - s * 0.8)} q${f(s * 0.05)},${f(-s * 0.5)} ${f(s * 0.35)},${f(-s * 0.7)}` }),
            React.createElement('circle', { cx: x + s * 0.95, cy: y - s * 0.5, r: s * 0.08, fill: '#1C1917' })));
    };

    // A faint rainbow behind the Cloud Tree
    const drawRainbow = () => {
        if (stage < 0.6) return;
        const cx = 100, cy = GROUND - 4, R = Math.max(36, (box.x1 - box.x0) * 0.46);
        ['#F87171', '#FBBF24', '#FDE047', '#4ADE80', '#60A5FA', '#A78BFA'].forEach((c, i) => {
            const r = R - i * 2.6;
            ground.push(React.createElement('path', { key: `rb-${i}`, fill: 'none', stroke: c, strokeWidth: 2.6, opacity: 0.4, d: `M${f(cx - r)},${f(cy)} A${f(r)},${f(r)} 0 0 1 ${f(cx + r)},${f(cy)}` }));
        });
    };
    // ---- end second grove art ----

    const renderTree = () => {
        const base = look.pot ? POT : GROUND;
        const pot = look.pot ? potEls() : [];
        if (stage < 0.05) {
            // Seed resting in a little mound of soil
            return [
                React.createElement('ellipse', { key: 'soil', cx: 100, cy: base, rx: 12, ry: 4, fill: '#8D6E63', opacity: 0.6 }),
                React.createElement('ellipse', { key: 'seed', className: 'tree-leaf', cx: 100, cy: base - 3, rx: 3.5, ry: 2.6, fill: '#6D4C41', transform: `rotate(-20 100 ${base - 3})` }),
                ...pot
            ];
        }
        if (stage < 0.15) {
            // Sprout: a curling stem with two leaves
            const h = 10 + (stage - 0.05) * 220, tx = 100 + Math.sin(stage * 30) * 3;
            const sproutLeaf = ['circle', 'blade', 'triangle'].includes(shapes[0]) ? 'oval' : shapes[0];
            return [
                React.createElement('path', { key: 'stem', d: `M100,${base} Q${f(100 - 4)},${f(base - h / 2)} ${f(tx)},${f(base - h)}`, stroke: '#4D7C0F', strokeWidth: 2.2, fill: 'none', strokeLinecap: 'round' }),
                leaf('sl', sproutLeaf, tx - 5, base - h + 1, 5, leafColors[0], -30),
                leaf('sr', sproutLeaf, tx + 5, base - h - 1, 5.5, leafColors[1] || leafColors[0], 30),
                ...pot
            ];
        }
        if (look.form === 'weeping') drawWeeping();
        else if (look.form === 'conifer') drawConifer(false);
        else if (look.form === 'columnar') drawConifer(true);
        else if (look.form === 'baobab') drawBaobab();
        else if (look.form === 'umbrella') drawUmbrella();
        else if (look.form === 'palm') drawPalm();
        else if (look.form === 'bamboo') drawBamboo();
        else if (look.form === 'crystal') drawCrystal();
        else if (look.form === 'banyan') drawBanyan();
        else if (look.form === 'bonsai') drawBonsai();
        else if (look.form === 'marathon') drawMarathon();
        else if (look.form === 'world') drawWorld();
        else drawRound();
        drawFalling();
        if (look.bird) drawBird();
        if (look.moon) drawDisc('moon');
        if (look.sun) drawDisc('sun');
        if (look.rainbow) drawRainbow();
        if (look.motes) drawParticles(look.motes, 'tree-mote', 9, 1100);
        if (look.embers) drawParticles(look.embers, 'tree-ember', 11, 1200);
        if (look.fireflies) drawParticles(look.fireflies, 'tree-firefly', 10, 1300);
        if (look.owl) drawOwl();
        if (look.snow) drawSnow();
        if (look.halo && stage > 0.3) {
            const hr = Math.max(box.x1 - box.x0, GROUND - box.y0) * 0.55;
            ground.unshift(React.createElement('circle', { key: 'halo', className: 'tree-glow', cx: (box.x0 + box.x1) / 2, cy: box.y0 + (GROUND - box.y0) * 0.35, r: hr, fill: `url(#${haloId})` }));
        }
        return [...ground, ...canopy, ...branches, ...back, ...front, ...extras];
    };

    const barkStops = look.bark || [shadeHex(barkColor, 0.3), barkColor, tintHex(barkColor, 0.18), barkColor, shadeHex(barkColor, 0.35)];
    const drawn = renderTree();
    // Rare variant: a few soft four-point sparkles around the crown
    if (vr && stage >= 0.15) {
        for (let i = 0; i < 7; i++) {
            const x = box.x0 + rnd(900 + i) * (box.x1 - box.x0), y = box.y0 + rnd(910 + i) * (GROUND - box.y0) * 0.8, r = 2 + rnd(920 + i) * 2.2;
            drawn.push(React.createElement('path', {
                key: `rare-${i}`, className: 'tree-twinkle', fill: vr.sparkle, stroke: vr.badge, strokeWidth: 0.3, strokeOpacity: 0.5, style: { animationDelay: `${f(-i * 0.55)}s` },
                d: `M${f(x)},${f(y - r)} Q${f(x)},${f(y)} ${f(x + r)},${f(y)} Q${f(x)},${f(y)} ${f(x)},${f(y + r)} Q${f(x)},${f(y)} ${f(x - r)},${f(y)} Q${f(x)},${f(y)} ${f(x)},${f(y - r)} Z`
            }));
        }
    }
    // Keep a fully grown tree inside the card: shrink it toward its base if it would overflow
    const fit = Math.min(1, 112 / Math.max(1, 100 - box.x0, box.x1 - 100), (GROUND - 8) / Math.max(1, GROUND - box.y0));
    // Northern lights: wavy curtains across the sky, outside the fitted tree so they always span the card
    const curtain = (k) => {
        const top = [], bot = [];
        for (let i = 0; i <= 12; i++) {
            const x = -20 + i * 20, ph = k * 1.7;
            const yt = 20 + k * 13 + Math.sin(i * 0.7 + ph) * 9 + Math.sin(i * 1.9 + ph) * 3;
            top.push(`${f(x)},${f(yt)}`);
            bot.unshift(`${f(x)},${f(yt + 36 + Math.sin(i * 1.1 + ph * 2) * 10)}`);
        }
        return `M${top.join(' L')} L${bot.join(' L')} Z`;
    };

    return React.createElement('svg', {
        viewBox: "0 0 200 240",
        className: "w-full h-full tree-svg",
        style: { overflow: 'visible', position: 'relative', zIndex: 1 }
    },
        React.createElement('defs', null,
            React.createElement('linearGradient', { id: barkId, x1: 0, y1: 0, x2: 1, y2: 0 },
                barkStops.map((c, i) => React.createElement('stop', { key: i, offset: `${(i / (barkStops.length - 1)) * 100}%`, stopColor: c }))),
            look.halo && React.createElement('radialGradient', { id: haloId },
                React.createElement('stop', { offset: '0%', stopColor: look.halo, stopOpacity: 0.55 }),
                React.createElement('stop', { offset: '100%', stopColor: look.halo, stopOpacity: 0 })),
            look.aurora && React.createElement('linearGradient', { id: auroraId, x1: 0, y1: 0, x2: 0, y2: 1 },
                [['0%', '#C084FC', 0], ['25%', '#A78BFA', 0.5], ['55%', '#34D399', 0.75], ['100%', '#2DD4BF', 0]].map(([o, c, a]) =>
                    React.createElement('stop', { key: o, offset: o, stopColor: c, stopOpacity: a }))),
            look.aurora && React.createElement('filter', { id: `${auroraId}-blur`, x: '-10%', y: '-30%', width: '120%', height: '160%' },
                React.createElement('feGaussianBlur', { stdDeviation: 2.5 })),
            // soften the left and right ends so the lights fade into the sky
            look.aurora && React.createElement('linearGradient', { id: `${auroraId}-h`, x1: 0, y1: 0, x2: 1, y2: 0 },
                [['0%', 0], ['22%', 1], ['78%', 1], ['100%', 0]].map(([o, a]) =>
                    React.createElement('stop', { key: o, offset: o, stopColor: '#FFFFFF', stopOpacity: a }))),
            look.aurora && React.createElement('mask', { id: `${auroraId}-fade` },
                React.createElement('rect', { x: 0, y: 0, width: 200, height: 240, fill: `url(#${auroraId}-h)` }))
        ),
        look.aurora && stage > 0.15 && React.createElement('g', { opacity: Math.min(1, stage * 1.4), mask: `url(#${auroraId}-fade)`, filter: `url(#${auroraId}-blur)` },
            React.createElement('g', { className: 'tree-aurora' },
                [0.9, 0.6, 0.45].map((o, k) => React.createElement('path', { key: k, fill: `url(#${auroraId})`, opacity: o, d: curtain(k) })))),
        // Grass mound and the tree's shadow
        React.createElement('ellipse', { cx: 100, cy: GROUND + 3, rx: 70, ry: 8, fill: '#4D7C0F', opacity: look.night ? 0.35 : 0.18 }),
        React.createElement('ellipse', { cx: 100, cy: GROUND + 1, rx: 14 + 50 * stage, ry: 5, fill: '#000', opacity: 0.12 }),
        [-52, -38, 34, 50].map((dx, i) => React.createElement('path', {
            key: `g-${i}`, d: `M${100 + dx},${GROUND + 3} l-2,-5 M${100 + dx},${GROUND + 3} l1,-6 M${100 + dx},${GROUND + 3} l3,-4`,
            stroke: '#3F6212', strokeWidth: 1, strokeLinecap: 'round', opacity: 0.5
        })),
        // Sways gently while a timer is running
        React.createElement('g', { className: isGrowing ? 'tree-sway' : '' },
            React.createElement('g', { transform: fit < 1 ? `translate(100 ${GROUND}) scale(${fit.toFixed(3)}) translate(-100 -${GROUND})` : undefined }, drawn))
    );
});

// ---------------------------------------------------------------------------
// Tree unlock moment: a full-screen celebration when study hours unlock a new tree,
// plus a shareable 1080x1350 PNG card. Self-contained: other features can call
// celebrateTreeUnlock(treeId, { hours }) (also on window), and window.__nousCelebrate('banyan')
// previews it from the console.
// ---------------------------------------------------------------------------


function renderNousTreeSVG(treeType, pct, isGrowing) {
    const typeProps = TREE_TYPES.find(t => t.id === treeType) || TREE_TYPES[0];
    const color = typeProps.color || "#4a7c2c";
    return TreeSVG({
        growth: Math.max(0, Math.min(100, pct)),
        color: color,
        treeType: typeProps.id,
        isGrowing: !!isGrowing,
        variant: null
    });
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderNousTreeSVG, TREE_TYPES, TREE_LOOKS };
}

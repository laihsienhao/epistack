import json
import textwrap
from collections import defaultdict

from streamlit_agraph import Config, Edge, Node
from streamlit_agraph import _agraph as _agraph_component

from src.crux import compute_cruxes
from src.loader import Graph, compute_depths, reachable_roots

# Stable widget key for the graph component -- deliberately never changes
# (see detail_panel.py's dismiss handler for why this matters: it lets us
# reset the tracked click value without remounting the component).
GRAPH_WIDGET_KEY = "agraph_graph"

# The dataviz skill's validated categorical palette, in its documented fixed
# order -- never reordered or cycled, since that order is what its CVD-safety
# validation is computed against. Also names blue<->red as the designated
# diverging pair, which is the correct encoding for exactly two opposing
# theses (see _root_hues): reserve red for that role rather than spending it
# as an ordinary 3rd+ category slot.
CATEGORICAL_HUES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
# Off the palette's stock blue/red entirely -- both the original saturated
# primary pair (clashing crayon-box look) and a muted navy/terracotta pass
# (read as flat and lifeless) missed the mark against the app's cream
# background. Indigo/coral is a warm/cool jewel-tone pair instead: saturated
# enough to stay lively, still two clearly distinct, non-red-green hues
# (colorblind safe), and clear of the amber/near-black crux border colors.
DIVERGING_PAIR = ("#4b4a8f", "#e0724f")  # indigo, coral

# Warm stone/taupe instead of a cool pure gray -- same lightness as the old
# gray (so white text and overall visual weight stay unchanged), but the
# warmer undertone sits with the cream background instead of against it.
NEUTRAL_FILL = "#8f8571"  # shared ground-truths / double cruxes belong to no single side

# Non-root claims tint their side's hue toward this instead of pure white, so
# the lightened fills read as warm paper tones consistent with the page
# background rather than a chalky, mismatched pale blue/red.
TINT_TARGET = "#faf6ec"

# Crux status is a small fixed scale, so it borrows a track separate from the
# side hues entirely (amber -> near-black), never blue/red.
NO_CRUX_BORDER = "#c3c2b7"
CRUX_BORDER = "#fab219"
DOUBLE_CRUX_BORDER = "#0b0b0b"

TEXT_ON_DARK = "#ffffff"
TEXT_ON_LIGHT = "#0b0b0b"

WRAP_WIDTH = 20

NODE_GAP = 200
LEVEL_HEIGHT = 250
BLOCK_MARGIN = 100  # small extra buffer between adjacent root blocks, on top of
# the per-depth neutral clearance _compute_positions already guarantees
SPLIT_THRESHOLD = 4  # side-groups larger than this split into two stacked rows,
# to keep any one tier from stretching too wide
SPLIT_GAP = NODE_GAP  # vertical gap between a split tier's two rows -- kept
# small and equal to NODE_GAP on purpose, so the two rows still read as one
# tier rather than an extra level. Clearance from the neutral column (which
# sits at the midpoint, closer than NODE_GAP away vertically) comes from
# horizontal separation instead -- see half_width below, which always
# reserves that regardless of whether a row is split.


def _wrap(text: str, width: int = WRAP_WIDTH) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _lighten(hex_color: str, amount: float = 0.55, target: str = TINT_TARGET) -> str:
    hex_color = hex_color.lstrip("#")
    target = target.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    tr, tg, tb = (int(target[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (t - c) * amount) for c, t in zip((r, g, b), (tr, tg, tb)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _text_color_for(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return TEXT_ON_LIGHT if luminance > 0.55 else TEXT_ON_DARK


def _root_hues(roots: list[str]) -> dict[str, str]:
    """One hue per "school of thought" (root). Exactly two roots is polarity --
    two opposing theses -- so it gets the palette's actual diverging pair.
    Three or more is plain categorical identity, so it draws from the fixed
    8-hue order in sequence, never reordered."""
    roots_sorted = sorted(roots)
    if len(roots_sorted) == 2:
        return dict(zip(roots_sorted, DIVERGING_PAIR))
    return {root: CATEGORICAL_HUES[i % len(CATEGORICAL_HUES)] for i, root in enumerate(roots_sorted)}


def _claim_side(claim_id: str, reached: dict[str, set[str]]) -> str | None:
    """The single root a claim belongs to, or None if shared/neutral."""
    own_roots = reached.get(claim_id, set())
    return next(iter(own_roots)) if len(own_roots) == 1 else None


def _side_fill(claim_id: str, roots: set[str], reached: dict[str, set[str]], root_hues: dict[str, str]) -> str:
    side = _claim_side(claim_id, reached)
    if side is None:
        return NEUTRAL_FILL
    hue = root_hues[side]
    return hue if claim_id in roots else _lighten(hue)


def _offset_max(members: list[str]) -> float:
    """How far a row's outermost member sits from its own center, given
    NODE_GAP spacing -- i.e. that row's half-footprint, measured center to
    center like every other NODE_GAP gap in this layout."""
    count = len(members)
    return ((count - 1) / 2) * NODE_GAP if count else 0.0


def _compute_positions(
    graph: Graph, roots: set[str], reached: dict[str, set[str]], depths: dict[str, int]
) -> dict[str, tuple[float, float]]:
    """Manually lay out nodes: y from depth (root at top), x clustered by side
    so each side's claims sit under its own root instead of vis-network's
    generic hierarchical solver interleaving them.

    Root anchors are spaced dynamically from the data rather than a fixed
    constant, so a case with few claims per side compacts much tighter than
    one with many. A side's row at a given depth splits into two stacked rows
    once it has more than SPLIT_THRESHOLD members, to keep any one tier from
    stretching too wide horizontally -- the neutral/shared column at that
    depth stays a single row, centered vertically between the two split rows
    (see SPLIT_GAP).

    Within a row, members are ordered by *barycenter* -- the average x of the
    node(s) each one points to -- rather than alphabetically by id. Every
    edge points to a strictly shallower depth (see compute_depths), so
    processing depths shallow-to-deep means a claim's targets are always
    already positioned by the time it needs ordering. This is the standard
    layered-graph-drawing heuristic for cutting down edge crossings; sorting
    by id instead (the previous approach) put a claim's x position at no
    relation to what it actually points to, which is what made the arrows
    hard to visually trace once the graph grew past a handful of claims per
    row."""
    groups: dict[tuple[int, str | None], list[str]] = defaultdict(list)
    for cid in graph.claims:
        groups[(depths[cid], _claim_side(cid, reached))].append(cid)

    # Row *sizing* only needs counts, not final member order -- actual member
    # assignment happens later, once barycenters are available (see the
    # position-filling loop at the bottom).
    split_depths = {depth for (depth, side), members in groups.items() if side is not None and len(members) > SPLIT_THRESHOLD}

    # Each depth occupies a vertical "band" -- zero height normally (a single
    # row), or SPLIT_GAP tall when split (two rows, that far apart). Bands
    # stack with a constant LEVEL_HEIGHT gap between the bottom of one and the
    # top of the next, so a split tier pushes everything below it down rather
    # than risking a collision.
    all_depths = sorted({d for d, _s in groups})
    band_height = {d: (SPLIT_GAP if d in split_depths else 0.0) for d in all_depths}
    top: dict[int, float] = {}
    bottom = 0.0
    for i, d in enumerate(all_depths):
        top[d] = 0.0 if i == 0 else bottom + LEVEL_HEIGHT
        bottom = top[d] + band_height[d]

    neutral_offset_max = {depth: _offset_max(members) for (depth, side), members in groups.items() if side is None}

    roots_sorted = sorted(roots)
    half_width: dict[str, float] = {}
    for r in roots_sorted:
        terms = [NODE_GAP]
        for (depth, side), members in groups.items():
            if side != r:
                continue
            # Every row -- split or not -- keeps NODE_GAP horizontal
            # clearance from the neutral column at this depth. With SPLIT_GAP
            # kept small (see above), the vertical distance to a split row's
            # midpoint-seated neutral column isn't enough on its own, so
            # horizontal separation is what actually guarantees no overlap.
            terms.append(_offset_max(members) + neutral_offset_max.get(depth, 0.0) + NODE_GAP)
        half_width[r] = max(terms)

    # Pack roots outward from the neutral column at x=0 -- first half of the
    # sorted roots to the left (negative x), second half to the right
    # (positive x) -- each root positioned at exactly its own half_width (plus
    # BLOCK_MARGIN from any same-side sibling), so its widest row always
    # clears the neutral column regardless of how wide any other root's rows
    # are. A prior "pack cursor left-to-right, then shift by the average of
    # all root_x" approach diluted a very wide root's clearance whenever a
    # much narrower sibling root pulled that average back toward zero --
    # exactly the failure the numeric sanity check in CLAUDE.md is meant to
    # catch (see also the min-pairwise-distance check after any layout edit).
    root_x: dict[str, float] = {}
    split_index = (len(roots_sorted) + 1) // 2
    for sign, side_roots in ((-1.0, roots_sorted[:split_index]), (1.0, roots_sorted[split_index:])):
        cursor = 0.0
        for i, r in enumerate(side_roots):
            cursor += half_width[r]
            if i > 0:
                cursor += BLOCK_MARGIN
            root_x[r] = sign * cursor
            cursor += half_width[r]

    def _place_row(members: list[str], base_x: float, y: float, positions: dict[str, tuple[float, float]]) -> None:
        count = len(members)
        for i, cid in enumerate(members):
            offset = (i - (count - 1) / 2) * NODE_GAP
            positions[cid] = (base_x + offset, y)

    def _barycenter(cid: str, positions: dict[str, tuple[float, float]]) -> float:
        xs = [positions[edge.to][0] for edge in graph.outgoing(cid) if edge.to in positions]
        return sum(xs) / len(xs) if xs else 0.0

    # Depth 0 is always roots (a claim has depth 0 iff it has no outgoing
    # edges iff it's a root), each alone in its own (0, own_id) group, so no
    # ordering/barycenter is needed there -- root_x already fixes their x.
    # Every depth >= 1 group is ordered by the already-placed positions of
    # whatever its members point to, processed shallow-to-deep so a claim's
    # targets are always resolved before the claim itself needs ordering.
    positions: dict[str, tuple[float, float]] = {}
    for depth in all_depths:
        for (d, side), members in groups.items():
            if d != depth:
                continue
            if depth == 0:
                _place_row(members, root_x[side], top[depth], positions)
                continue

            ordered = sorted(members, key=lambda cid: (_barycenter(cid, positions), cid))

            if side is None:
                _place_row(ordered, 0.0, top[depth] + band_height[depth] / 2, positions)
            elif len(ordered) > SPLIT_THRESHOLD:
                # Interleave the barycenter-sorted order across both split
                # rows (rather than a contiguous first-half/second-half cut)
                # so each row still spans -- and reflects -- the full
                # left-to-right barycenter range instead of one row reading
                # systematically further left than the other.
                _place_row(ordered[0::2], root_x[side], top[depth], positions)
                _place_row(ordered[1::2], root_x[side], top[depth] + band_height[depth], positions)
            else:
                _place_row(ordered, root_x[side], top[depth], positions)

    return positions


def build_elements(
    graph: Graph,
    search_query: str = "",
    show_only_cruxes: bool = False,
) -> tuple[list[Node], list[Edge]]:
    """Translate a Graph into agraph Nodes/Edges with side and crux salience baked in.

    Position is fully manual (x from side-clustering, y from depth), fixed so
    physics/layout never moves it -- this guarantees each side's claims sit
    under their own root, which vis-network's automatic hierarchical solver
    does not reliably do when many nodes share a level. Zoom is handled
    entirely client-side (see zoom_controls.py) via a CSS transform on the
    rendered network -- not from here -- so zooming never triggers a rerun.
    """
    depths = compute_depths(graph)
    reached = reachable_roots(graph)
    crux_for = compute_cruxes(graph)
    roots = set(graph.roots())
    root_hues = _root_hues(list(roots))
    positions = _compute_positions(graph, roots, reached, depths)

    visible_ids = set(graph.claims)
    if search_query:
        q = search_query.lower()
        visible_ids = {cid for cid in visible_ids if q in graph.claims[cid].text.lower()}
    if show_only_cruxes:
        visible_ids &= set(crux_for) | roots

    nodes: list[Node] = []
    for cid in visible_ids:
        claim = graph.claims[cid]
        is_root = cid in roots
        crux_roots = crux_for.get(cid, set())
        is_double_crux = len(crux_roots) >= 2
        is_crux = bool(crux_roots)

        fill = _side_fill(cid, roots, reached, root_hues)
        text_color = _text_color_for(fill)

        if is_double_crux:
            border_color, border_width = DOUBLE_CRUX_BORDER, 5
        elif is_crux:
            border_color, border_width = CRUX_BORDER, 4
        else:
            border_color, border_width = NO_CRUX_BORDER, 1

        label = _wrap(claim.label)
        x, y = positions[cid]

        nodes.append(
            Node(
                id=cid,
                label=label,
                title=claim.text,
                x=x,
                y=y,
                fixed={"x": True, "y": True},
                shape="circle",
                size=40 if is_root else 26,
                color={"background": fill, "border": border_color},
                borderWidth=border_width,
                borderWidthSelected=border_width + 2,
                font={
                    "color": text_color,
                    "size": 17 if is_root else 14,
                    "face": "system-ui, -apple-system, sans-serif",
                    "multi": False,
                },
                margin=10,
            )
        )

    edges: list[Edge] = []
    for edge in graph.edges:
        if edge.from_ not in visible_ids or edge.to not in visible_ids:
            continue
        is_depends_on = edge.relation == "depends_on"
        edge_color = _side_fill(edge.to, roots, reached, root_hues)
        edges.append(
            Edge(
                source=edge.from_,
                target=edge.to,
                id=edge.id,
                color=edge_color,
                width=4 if is_depends_on else 1.5,
                dashes=not edge.provenance,
                smooth={"enabled": True, "type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.45},
            )
        )

    return nodes, edges


def render_graph(
    graph: Graph,
    search_query: str = "",
    show_only_cruxes: bool = False,
) -> str | None:
    nodes, edges = build_elements(graph, search_query, show_only_cruxes)
    config = Config(
        height=800,
        width=1400,
        directed=True,
        physics=False,
        hierarchical=False,
        groups={},
        # autoResize=False so a container resize (e.g. the network briefly
        # hidden/shown behind the dialog overlay) never triggers a re-fit that
        # would silently reset the user's zoom/pan -- it only affects re-fits
        # *after* the initial mount, so it's compatible with the width override
        # below, which only matters at that one initial `_setSize()` call.
        autoResize=False,
        interaction={
            "navigationButtons": False,
            "zoomView": True,
            "zoomSpeed": 0.25,
            "dragView": True,
            "keyboard": False,
        },
    )
    # Override the width Config just built to a CSS percentage instead of a
    # fixed pixel value -- Config.__init__ always suffixes its int argument
    # with "px", so there's no way to request this through the constructor.
    # Without this, the canvas frame is a literal fixed-pixel box regardless
    # of the actual column width it's embedded in, and it was previously wide
    # enough (2800px) to overflow past the page on typical screens.
    config.width = "100%"
    # Calling the raw declared component (rather than streamlit_agraph's own
    # agraph() wrapper, which doesn't forward key) so we can give it a
    # stable, explicit key. This keeps the same component instance across
    # reruns (filters, zoom, etc.) instead of Streamlit's default arg-hash
    # keying possibly remounting it when the data payload changes shape.
    data_json = json.dumps({"nodes": [n.to_dict() for n in nodes], "edges": [e.to_dict() for e in edges]})
    config_json = json.dumps(config.__dict__)
    return _agraph_component(data=data_json, config=config_json, key=GRAPH_WIDGET_KEY)

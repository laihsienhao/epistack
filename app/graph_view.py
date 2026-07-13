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

# One hue per "school of thought" (root), assigned in a fixed order. Blue/red
# is the palette's diverging pair -- exactly the right fit for two opposing
# theses. Amber/black (crux status, below) are deliberately excluded here so
# the two channels never collide.
SIDE_HUES = ["#2a78d6", "#e34948", "#4a3aa7", "#1baf7a", "#008300", "#e87ba4"]

NEUTRAL_FILL = "#898781"  # shared ground-truths / double cruxes belong to no single side

# Crux status is a small fixed scale, so it borrows a track separate from the
# side hues entirely (amber -> black), never blue/red.
NO_CRUX_BORDER = "#c3c2b7"
CRUX_BORDER = "#fab219"
DOUBLE_CRUX_BORDER = "#111111"

TEXT_ON_DARK = "#ffffff"
TEXT_ON_LIGHT = "#0b0b0b"

WRAP_WIDTH = 20

ROOT_SPACING = 1500
NODE_GAP = 170
LEVEL_HEIGHT = 250


def _wrap(text: str, width: int = WRAP_WIDTH) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _lighten(hex_color: str, amount: float = 0.55) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (255 - c) * amount) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _text_color_for(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return TEXT_ON_LIGHT if luminance > 0.55 else TEXT_ON_DARK


def _root_hues(roots: list[str]) -> dict[str, str]:
    return {root: SIDE_HUES[i % len(SIDE_HUES)] for i, root in enumerate(sorted(roots))}


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


def _compute_positions(
    graph: Graph, roots: set[str], reached: dict[str, set[str]], depths: dict[str, int]
) -> dict[str, tuple[float, float]]:
    """Manually lay out nodes: y from depth (root at top), x clustered by side
    so each side's claims sit under its own root instead of vis-network's
    generic hierarchical solver interleaving them."""
    roots_sorted = sorted(roots)
    n_roots = len(roots_sorted)
    root_x = {r: (i - (n_roots - 1) / 2) * ROOT_SPACING for i, r in enumerate(roots_sorted)}

    groups: dict[tuple[int, str | None], list[str]] = defaultdict(list)
    for cid in graph.claims:
        groups[(depths[cid], _claim_side(cid, reached))].append(cid)

    positions: dict[str, tuple[float, float]] = {}
    for (depth, side), members in groups.items():
        members_sorted = sorted(members)
        base_x = root_x[side] if side is not None else 0.0
        count = len(members_sorted)
        for i, cid in enumerate(members_sorted):
            offset = (i - (count - 1) / 2) * NODE_GAP
            positions[cid] = (base_x + offset, depth * LEVEL_HEIGHT)

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

        badge = "\n🔑🔑" if is_double_crux else ("\n🔑" if is_crux else "")
        label = _wrap(claim.label) + badge
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
        width=2800,
        directed=True,
        physics=False,
        hierarchical=False,
        groups={},
        # vis-network's default autoResize watches the container and re-fits
        # the view on any resize -- including the container being briefly
        # hidden/shown behind the dialog overlay, which was silently resetting
        # the user's zoom/pan every time a dialog closed. The canvas here is a
        # fixed size by design (see height/width above), so it never needs to
        # adapt to its container anyway.
        autoResize=False,
        interaction={
            "navigationButtons": False,
            "zoomView": True,
            "zoomSpeed": 0.25,
            "dragView": True,
            "keyboard": False,
        },
    )
    # Calling the raw declared component (rather than streamlit_agraph's own
    # agraph() wrapper, which doesn't forward key) so we can give it a
    # stable, explicit key. This keeps the same component instance across
    # reruns (filters, zoom, etc.) instead of Streamlit's default arg-hash
    # keying possibly remounting it when the data payload changes shape.
    data_json = json.dumps({"nodes": [n.to_dict() for n in nodes], "edges": [e.to_dict() for e in edges]})
    config_json = json.dumps(config.__dict__)
    return _agraph_component(data=data_json, config=config_json, key=GRAPH_WIDGET_KEY)

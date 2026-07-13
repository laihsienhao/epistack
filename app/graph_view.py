from streamlit_agraph import Config, Edge, Node, agraph

from src.crux import compute_cruxes
from src.loader import Graph, compute_depths, reachable_roots

ROOT_COLOR = "#1e3a5f"
SHARED_COLOR = "#e2e8f0"
DEFAULT_COLOR = "#94a3b8"

CRUX_BORDER = "#d97706"       # amber -- crux for one root
DOUBLE_CRUX_BORDER = "#b91c1c"  # red -- crux for >=2 roots
DEFAULT_BORDER = "#475569"

SUPPORTS_EDGE_COLOR = "#94a3b8"
DEPENDS_ON_EDGE_COLOR = "#d97706"


def _truncate(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_elements(
    graph: Graph,
    tag_filter: set[str] | None = None,
    search_query: str = "",
    show_only_cruxes: bool = False,
) -> tuple[list[Node], list[Edge]]:
    """Translate a Graph into agraph Nodes/Edges with crux/shared salience baked in.

    Vertical position is set explicitly via each node's `level` (computed
    depth, not inferred from vis-network's edge-direction default, which
    treats the edge's source as the parent -- the opposite of our
    specific-to-general edge direction). Arrow direction is left untouched
    so arrowheads still point at what a claim supports/depends on.
    """
    depths = compute_depths(graph)
    shared = reachable_roots(graph)
    crux_for = compute_cruxes(graph)
    roots = set(graph.roots())

    visible_ids = set(graph.claims)
    if tag_filter:
        visible_ids = {cid for cid in visible_ids if tag_filter & set(graph.claims[cid].tags)}
    if search_query:
        q = search_query.lower()
        visible_ids = {cid for cid in visible_ids if q in graph.claims[cid].text.lower()}
    if show_only_cruxes:
        visible_ids &= set(crux_for) | roots

    nodes: list[Node] = []
    for cid in visible_ids:
        claim = graph.claims[cid]
        is_root = cid in roots
        is_shared = len(shared.get(cid, set())) >= 2
        crux_roots = crux_for.get(cid, set())
        is_double_crux = len(crux_roots) >= 2
        is_crux = bool(crux_roots)

        if is_root:
            color = ROOT_COLOR
        elif is_shared:
            color = SHARED_COLOR
        else:
            color = DEFAULT_COLOR

        if is_double_crux:
            border_color, border_width = DOUBLE_CRUX_BORDER, 5
        elif is_crux:
            border_color, border_width = CRUX_BORDER, 3
        else:
            border_color, border_width = DEFAULT_BORDER, 1

        badge = " 🔑🔑" if is_double_crux else (" 🔑" if is_crux else "")
        nodes.append(
            Node(
                id=cid,
                label=_truncate(claim.text) + badge,
                title=claim.text,
                level=depths[cid],
                size=32 if is_root else 22,
                shape="dot",
                color={"background": color, "border": border_color},
                borderWidth=border_width,
                font={"color": "#0f172a" if color == SHARED_COLOR else "#f8fafc"},
            )
        )

    edges: list[Edge] = []
    for edge in graph.edges:
        if edge.from_ not in visible_ids or edge.to not in visible_ids:
            continue
        is_depends_on = edge.relation == "depends_on"
        edges.append(
            Edge(
                source=edge.from_,
                target=edge.to,
                id=edge.id,
                label="depends_on 🔑" if is_depends_on else "",
                color=DEPENDS_ON_EDGE_COLOR if is_depends_on else SUPPORTS_EDGE_COLOR,
                width=3 if is_depends_on else 1,
                dashes=not edge.provenance,
            )
        )

    return nodes, edges


def render_graph(
    graph: Graph,
    tag_filter: set[str] | None = None,
    search_query: str = "",
    show_only_cruxes: bool = False,
) -> str | None:
    nodes, edges = build_elements(graph, tag_filter, search_query, show_only_cruxes)
    config = Config(
        height=650,
        width=900,
        directed=True,
        physics=False,
        hierarchical=True,
        direction="UD",
        sortMethod="directed",
        levelSeparation=140,
        nodeSpacing=180,
        highlightColor="#f59e0b",
    )
    return agraph(nodes=nodes, edges=edges, config=config)

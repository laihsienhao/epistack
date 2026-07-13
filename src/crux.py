from collections import defaultdict

from .loader import Graph


def compute_cruxes(graph: Graph) -> dict[str, set[str]]:
    """Map claim id -> set of root ids it is a crux for.

    A claim is a crux for a root if there is a path of `depends_on`-only
    edges from the claim up to the root — falsifying it breaks a necessary
    condition in the chain, rather than merely weakening a supporting
    argument. No stored field: this is a pure traversal over the edges
    already in the graph.
    """
    depends_on_children: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.relation == "depends_on":
            depends_on_children[edge.to].append(edge.from_)

    crux_for: dict[str, set[str]] = defaultdict(set)
    for root in graph.roots():
        stack = list(depends_on_children.get(root, []))
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            crux_for[node].add(root)
            stack.extend(depends_on_children.get(node, []))

    return dict(crux_for)


def double_cruxes(graph: Graph) -> set[str]:
    """Claims that are a crux for two or more distinct roots.

    A strict subset of the graph's shared ground-truth claims: the rare,
    high-value case where a single unresolved question would move more than
    one school of thought if it were settled.
    """
    return {claim_id for claim_id, roots in compute_cruxes(graph).items() if len(roots) >= 2}

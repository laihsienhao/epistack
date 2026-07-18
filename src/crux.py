from collections import defaultdict
from typing import Iterable

from .loader import Graph


def compute_cruxes_for(graph: Graph, reference_points: Iterable[str]) -> dict[str, set[str]]:
    """Map claim id -> set of reference points it is a crux for.

    A claim is a crux for a reference point if there is a path of
    `depends_on`-only edges from the claim up to that point — falsifying it
    breaks a necessary condition in the chain, rather than merely weakening
    a supporting argument. No stored field: this is a pure traversal over
    the edges already in the graph.

    Generalizes `compute_cruxes` (which always uses root theses) to any
    reference point, including non-root "sub-thesis" nodes (see
    `sub_thesis_nodes`). This matters because broadening a thesis to rest
    on several independently-sufficient pillars can make a genuinely
    load-bearing claim invisible when only checked against the top-level
    roots — see CLAUDE.md's "Crux/root-count consequences of broadening a
    thesis" for the eggs case this was discovered on. Checking against
    sub-thesis reference points too recovers exactly that claim, scoped to
    its own narrower branch, without changing what "crux" means.
    """
    depends_on_children: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.relation == "depends_on":
            depends_on_children[edge.to].append(edge.from_)

    crux_for: dict[str, set[str]] = defaultdict(set)
    for ref in reference_points:
        stack = list(depends_on_children.get(ref, []))
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            crux_for[node].add(ref)
            stack.extend(depends_on_children.get(node, []))

    return dict(crux_for)


def compute_cruxes(graph: Graph) -> dict[str, set[str]]:
    """Map claim id -> set of root ids it is a crux for.

    The root-only special case of `compute_cruxes_for` — this is the one the
    Cruxes tab and `double_cruxes` use, since "load-bearing for a whole
    school of thought" is the flagship reading. See `compute_cruxes_for` for
    the general version and `src/research_priorities.py` for where checking
    sub-thesis reference points too becomes valuable.
    """
    return compute_cruxes_for(graph, graph.roots())


def double_cruxes(graph: Graph) -> set[str]:
    """Claims that are a crux for two or more distinct roots.

    A strict subset of the graph's shared ground-truth claims: the rare,
    high-value case where a single unresolved question would move more than
    one school of thought if it were settled.
    """
    return {claim_id for claim_id, roots in compute_cruxes(graph).items() if len(roots) >= 2}


def sub_thesis_nodes(graph: Graph) -> list[str]:
    """Non-root claims that synthesize 2+ incoming edges -- structural
    "sub-theses" worth treating as their own crux reference points,
    alongside root theses.

    Derived purely from edge in-degree, no new tag or schema field: a claim
    multiple other claims feed into (rather than one that just points
    outward toward its own root) is functioning as a synthesizing hub in
    the argument, the same role a root plays for the whole graph, just
    scoped narrower. Verified against the real `eggs` case: this picks out
    exactly `eggs-fine-in-moderation` and `eggs-should-be-limited` (each fed
    by the shared cholesterol-content/response-variability facts plus the
    cholesterol-causal-effect double-crux) with no noise.
    """
    roots = set(graph.roots())
    return [cid for cid in graph.claims if cid not in roots and len(graph.incoming(cid)) >= 2]

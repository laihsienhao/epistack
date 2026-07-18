from .crux import compute_cruxes_for, sub_thesis_nodes
from .loader import Graph


def _upstream_size(graph: Graph, target: str) -> int:
    """How many distinct claims ultimately feed into `target`, transitively
    (following incoming edges of any relation, not just depends_on) -- a
    proxy for how much of the graph's argument structure routes through it,
    used to weight research priorities by impact, not just by crux status
    alone."""
    seen: set[str] = set()
    stack = [edge.from_ for edge in graph.incoming(target)]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edge.from_ for edge in graph.incoming(node))
    return len(seen)


def research_priorities(graph: Graph) -> list[dict]:
    """Rank claims by how much future research resolving them would matter.

    Reuses crux detection (`src/crux.py`) but relative to BOTH root theses
    and sub-thesis nodes as reference points, since broadening a thesis to
    rest on independently-sufficient pillars can make a genuinely
    load-bearing claim invisible at the top-level-root view alone (see
    CLAUDE.md's "Crux/root-count consequences of broadening a thesis").
    Excludes claims tagged `contextual` -- per this project's own tag
    vocabulary (`docs/CONTRIBUTING_CLAIMS.md`), those are apparent conflicts
    that resolve once a variable is specified, not open research questions;
    only genuinely unresolved (`contested` or untagged) cruxes are research
    targets.

    Ranked by (a) how many reference points a claim is load-bearing for
    (a claim load-bearing for 2+ is the generalized double-crux case), then
    (b) total upstream size summed across those reference points, as a
    proxy for how much of the graph's argument structure would move if it
    were resolved.

    Returns a list of dicts (not just ids) since the ranking signal itself
    -- reference points and impact -- is exactly what a caller needs to
    display, not something to recompute.
    """
    reference_points = list(graph.roots()) + sub_thesis_nodes(graph)
    crux_for = compute_cruxes_for(graph, reference_points)

    priorities: list[dict] = []
    for claim_id, refs in crux_for.items():
        claim = graph.claims.get(claim_id)
        if claim is None or "contextual" in claim.tags:
            continue
        impact = sum(_upstream_size(graph, ref) for ref in refs)
        priorities.append(
            {
                "claim_id": claim_id,
                "reference_points": sorted(refs),
                "impact": impact,
            }
        )

    priorities.sort(key=lambda p: (-len(p["reference_points"]), -p["impact"], p["claim_id"]))
    return priorities

from collections import defaultdict

from .loader import Graph, reachable_roots

TOPIC_PREFIX = "topic:"

# Known acronyms that shouldn't just be title-cased like an ordinary word,
# shared by every UI surface that renders a topic tag as a readable label.
_TOPIC_ACRONYMS = {"tmao", "t2d"}


def topic_label(tag: str) -> str:
    words = tag.removeprefix(TOPIC_PREFIX).split("-")
    return " ".join(w.upper() if w in _TOPIC_ACRONYMS else w.capitalize() for w in words)


def topic_coverage(graph: Graph) -> dict[str, set[str]]:
    """Map topic tag -> set of root ids whose reachable subtree contains a
    claim carrying that tag.

    Discourse structure -- which sub-questions each "side" of a debate
    actually engages with -- isn't visible from supports/depends_on edges
    alone, since a side can simply never build a branch on a topic its rival
    addresses. This surfaces that: a topic present in >=2 roots' coverage is
    a genuinely shared/contested sub-question both sides engage with (even if
    they reach opposite conclusions); a topic present in exactly one is a
    sub-question only that side has built out. No stored field -- pure
    traversal over `claim.tags` entries prefixed 'topic:', reusing the same
    reachable_roots() traversal cruxes and shared-ground-truths are built
    from.
    """
    reached = reachable_roots(graph)
    coverage: dict[str, set[str]] = defaultdict(set)
    for cid, claim in graph.claims.items():
        roots_for_claim = reached.get(cid, set())
        if not roots_for_claim:
            continue
        for tag in claim.tags:
            if tag.startswith(TOPIC_PREFIX):
                coverage[tag] |= roots_for_claim
    return dict(coverage)


def shared_topics(graph: Graph) -> set[str]:
    """Topics reachable from >=2 roots -- genuinely contested sub-questions
    both sides engage with, as opposed to a side's own one-sided branch."""
    return {topic for topic, roots in topic_coverage(graph).items() if len(roots) >= 2}


def topic_emphasis(graph: Graph) -> dict[str, dict[str, dict[str, int]]]:
    """Map topic tag -> root id -> {"claims": n, "sources": n}.

    topic_coverage() is deliberately binary -- a root either reaches a topic
    or it doesn't -- which captures *explicit* differences of emphasis (both
    sides address choline, but reach opposite conclusions) but not *implicit*
    ones: two roots can both "cover" the same topic while one has five claims
    and a dozen sources behind it and the other has exactly one. This is that
    second, weighted view -- still a pure traversal, no stored field, just
    counting instead of only checking reachability.
    """
    reached = reachable_roots(graph)
    emphasis: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for cid, claim in graph.claims.items():
        roots_for_claim = reached.get(cid, set())
        if not roots_for_claim:
            continue
        for tag in claim.tags:
            if not tag.startswith(TOPIC_PREFIX):
                continue
            for root in roots_for_claim:
                counts = emphasis[tag].setdefault(root, {"claims": 0, "sources": 0})
                counts["claims"] += 1
                counts["sources"] += len(claim.sources)
    return {tag: dict(roots) for tag, roots in emphasis.items()}

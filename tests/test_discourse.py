from datetime import date

from src.discourse import shared_topics, topic_coverage, topic_emphasis, topic_label
from src.loader import Graph
from src.models import Claim, Edge


def _claim(id_, tags=None, sources=None):
    return Claim(
        id=id_,
        case="synthetic",
        text=id_,
        label=id_,
        tags=tags or [],
        sources=sources or [],
        author="tester",
        created=date(2026, 7, 13),
    )


def _edge(id_, from_, to, relation="supports"):
    return Edge(id=id_, relation=relation, from_=from_, to=to, author="tester", created=date(2026, 7, 13))


def test_topic_reachable_from_one_root_only():
    claims = {
        "root-a": _claim("root-a"),
        "root-b": _claim("root-b"),
        "leaf-a": _claim("leaf-a", tags=["topic:widgets"]),
    }
    edges = [_edge("e1", "leaf-a", "root-a")]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    coverage = topic_coverage(graph)
    assert coverage["topic:widgets"] == {"root-a"}
    assert shared_topics(graph) == set()


def test_topic_reachable_from_two_roots_is_shared():
    claims = {
        "root-a": _claim("root-a"),
        "root-b": _claim("root-b"),
        "leaf-a": _claim("leaf-a", tags=["topic:widgets"]),
        "leaf-b": _claim("leaf-b", tags=["topic:widgets"]),
    }
    edges = [
        _edge("e1", "leaf-a", "root-a"),
        _edge("e2", "leaf-b", "root-b"),
    ]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    coverage = topic_coverage(graph)
    assert coverage["topic:widgets"] == {"root-a", "root-b"}
    assert shared_topics(graph) == {"topic:widgets"}


def test_topic_tag_on_unreachable_claim_is_ignored():
    # a claim with no outgoing edges at all, other than being its own root,
    # doesn't leak a topic tag onto some other root's coverage
    claims = {
        "root-a": _claim("root-a"),
        "orphan": _claim("orphan", tags=["topic:widgets"]),
    }
    graph = Graph(case_id="synthetic", claims=claims, edges=[], sources={})
    coverage = topic_coverage(graph)
    # "orphan" is itself a root (no outgoing edges), reachable only from
    # itself -- its topic tag shows up scoped to its own root, not root-a's
    assert coverage.get("topic:widgets") == {"orphan"}
    assert "root-a" not in coverage.get("topic:widgets", set())


def test_non_topic_tags_are_ignored():
    claims = {
        "root-a": _claim("root-a"),
        "leaf-a": _claim("leaf-a", tags=["contested", "ground-truth"]),
    }
    edges = [_edge("e1", "leaf-a", "root-a")]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    assert topic_coverage(graph) == {}


def test_topic_label_formats_hyphenated_names():
    assert topic_label("topic:saturated-fat") == "Saturated Fat"


def test_topic_label_uppercases_known_acronyms():
    assert topic_label("topic:tmao") == "TMAO"


def test_topic_emphasis_counts_claims_and_sources_per_root():
    claims = {
        "root-a": _claim("root-a"),
        "root-b": _claim("root-b"),
        # root-a: one thin claim on the topic
        "leaf-a": _claim("leaf-a", tags=["topic:widgets"], sources=["s1"]),
        # root-b: two claims on the same topic, more sources behind it
        "leaf-b1": _claim("leaf-b1", tags=["topic:widgets"], sources=["s2", "s3"]),
        "leaf-b2": _claim("leaf-b2", tags=["topic:widgets"], sources=["s4"]),
    }
    edges = [
        _edge("e1", "leaf-a", "root-a"),
        _edge("e2", "leaf-b1", "root-b"),
        _edge("e3", "leaf-b2", "root-b"),
    ]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    emphasis = topic_emphasis(graph)
    assert emphasis["topic:widgets"]["root-a"] == {"claims": 1, "sources": 1}
    assert emphasis["topic:widgets"]["root-b"] == {"claims": 2, "sources": 3}

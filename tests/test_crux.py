from datetime import date

from src.crux import compute_cruxes, compute_cruxes_for, double_cruxes, sub_thesis_nodes
from src.loader import Graph, load_case
from src.models import Claim, Edge


def test_compute_cruxes_on_toy_case():
    graph = load_case("toy")
    cruxes = compute_cruxes(graph)
    assert cruxes["long-term-mortality-data-favor-coffee"] == {"coffee-is-healthy"}
    assert cruxes["coffee-net-mortality-effect-contested"] == {
        "coffee-is-healthy",
        "coffee-is-harmful",
    }
    # shared via supports-only edges, not a crux
    assert "coffee-contains-caffeine" not in cruxes


def test_double_cruxes_on_toy_case():
    graph = load_case("toy")
    assert double_cruxes(graph) == {"coffee-net-mortality-effect-contested"}


def test_sub_thesis_nodes_on_eggs_case():
    # regression-anchors the real finding this feature was built around: the
    # broadened eggs roots hide cholesterol-causal-effect-contested as a
    # crux, but it reappears once these two sub-theses are also checked.
    graph = load_case("eggs")
    assert set(sub_thesis_nodes(graph)) == {"eggs-fine-in-moderation", "eggs-should-be-limited"}


def test_compute_cruxes_for_sub_thesis_reference_points_on_eggs_case():
    graph = load_case("eggs")
    assert compute_cruxes(graph) == {}  # broadened roots hide it (see CLAUDE.md)
    sub_theses = sub_thesis_nodes(graph)
    cruxes = compute_cruxes_for(graph, sub_theses)
    assert cruxes["cholesterol-causal-effect-contested"] == set(sub_theses)


def _claim(id_, tags=None):
    return Claim(
        id=id_, case="synthetic", text=id_, label=id_, tags=tags or [], author="tester", created=date(2026, 7, 13)
    )


def _edge(id_, from_, to, relation):
    return Edge(id=id_, relation=relation, from_=from_, to=to, author="tester", created=date(2026, 7, 13))


def test_no_cruxes_when_no_depends_on_edges():
    claims = {"root": _claim("root"), "leaf": _claim("leaf")}
    edges = [_edge("e1", "leaf", "root", "supports")]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    assert compute_cruxes(graph) == {}
    assert double_cruxes(graph) == set()


def test_crux_chain_transitivity():
    # grandchild -depends_on-> child -depends_on-> root: grandchild is still a crux for root
    claims = {"root": _claim("root"), "child": _claim("child"), "grandchild": _claim("grandchild")}
    edges = [
        _edge("e1", "child", "root", "depends_on"),
        _edge("e2", "grandchild", "child", "depends_on"),
    ]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    cruxes = compute_cruxes(graph)
    assert cruxes["child"] == {"root"}
    assert cruxes["grandchild"] == {"root"}


def test_sub_thesis_nodes_requires_two_incoming_edges_and_excludes_roots():
    claims = {
        "root": _claim("root"),
        "hub": _claim("hub"),  # 2 incoming -> qualifies
        "one-incoming": _claim("one-incoming"),  # only 1 incoming -> doesn't
        "fact-a": _claim("fact-a"),
        "fact-b": _claim("fact-b"),
    }
    edges = [
        _edge("e1", "hub", "root", "supports"),
        _edge("e2", "fact-a", "hub", "supports"),
        _edge("e3", "fact-b", "hub", "supports"),
        _edge("e4", "one-incoming", "root", "supports"),
        _edge("e5", "fact-a", "one-incoming", "supports"),
    ]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    assert sub_thesis_nodes(graph) == ["hub"]

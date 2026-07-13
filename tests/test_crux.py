from datetime import date

from src.crux import compute_cruxes, double_cruxes
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


def _claim(id_):
    return Claim(id=id_, case="synthetic", text=id_, label=id_, author="tester", created=date(2026, 7, 13))


def _edge(id_, from_, to, relation):
    return Edge(id=id_, relation=relation, from_=from_, to=to, author="tester", created=date(2026, 7, 13))


def test_no_cruxes_when_no_depends_on_edges():
    claims = {"root": _claim("root"), "leaf": _claim("leaf")}
    edges = [_edge("e1", "leaf", "root", "supports")]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    assert compute_cruxes(graph) == {}
    assert double_cruxes(graph) == set()


def test_crux_chain_transitivity():
    # grandchild -depends_on-> child -depends_on-> root: grandchild is still a crux for root
    claims = {"root": _claim("root"), "child": _claim("child"), "grandchild": _claim("grandchild")}
    edges = [
        _edge("e1", "child", "root", "depends_on"),
        _edge("e2", "grandchild", "child", "depends_on"),
    ]
    graph = Graph(case_id="synthetic", claims=claims, edges=edges, sources={})
    cruxes = compute_cruxes(graph)
    assert cruxes["child"] == {"root"}
    assert cruxes["grandchild"] == {"root"}

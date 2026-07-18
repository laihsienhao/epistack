import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from datetime import date

import graph_view

from src.loader import Graph
from src.models import Claim, Edge


def _claim(id_, tags=None):
    return Claim(
        id=id_,
        case="synthetic",
        text=id_,
        label=id_,
        tags=tags or [],
        author="tester",
        created=date(2026, 7, 13),
    )


def _edge(id_, from_, to, relation="supports"):
    return Edge(id=id_, relation=relation, from_=from_, to=to, author="tester", created=date(2026, 7, 13))


def _graph():
    claims = {
        "root-a": _claim("root-a"),
        "root-b": _claim("root-b"),
        "leaf-cholesterol": _claim("leaf-cholesterol", tags=["topic:cholesterol"]),
        "leaf-tmao": _claim("leaf-tmao", tags=["topic:tmao", "topic:choline"]),
        "leaf-untagged": _claim("leaf-untagged"),
    }
    edges = [
        _edge("e1", "leaf-cholesterol", "root-a"),
        _edge("e2", "leaf-tmao", "root-b"),
        _edge("e3", "leaf-untagged", "root-b"),
    ]
    return Graph(case_id="synthetic", claims=claims, edges=edges, sources={})


def test_topic_filter_shows_only_matching_claims_plus_roots():
    # root theses are the graph's top-level "schools of thought" -- always
    # shown regardless of any filter, so a reader never loses track of which
    # sides a filtered-down claim belongs to.
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=["topic:cholesterol"])
    ids = {n.id for n in nodes}
    assert ids == {"leaf-cholesterol", "root-a", "root-b"}


def test_topic_filter_is_or_across_multiple_topics():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=["topic:cholesterol", "topic:tmao"])
    ids = {n.id for n in nodes}
    assert ids == {"leaf-cholesterol", "leaf-tmao", "root-a", "root-b"}


def test_no_topic_filter_shows_everything():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=None)
    ids = {n.id for n in nodes}
    assert ids == set(graph.claims)


def test_topic_filter_combines_with_crux_filter_but_roots_still_show():
    # a claim matching the topic but not a crux is excluded once both
    # filters are active -- filters intersect, they don't OR across kinds --
    # but roots are exempt from every filter, so they remain.
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, show_only_cruxes=True, topic_filter=["topic:cholesterol"])
    ids = {n.id for n in nodes}
    assert ids == {"root-a", "root-b"}


def test_roots_survive_a_non_matching_search():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, search_query="text that matches nothing")
    ids = {n.id for n in nodes}
    assert ids == {"root-a", "root-b"}

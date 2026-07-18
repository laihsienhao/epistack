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
    return Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})


def test_topic_filter_shows_only_matching_claims_plus_roots():
    # root theses are the graph's top-level "schools of thought" -- always
    # shown regardless of any filter, so a reader never loses track of which
    # sides a filtered-down claim belongs to.
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=["topic:cholesterol"])
    ids = {n.id for n in nodes} - {"__question__"}
    assert ids == {"leaf-cholesterol", "root-a", "root-b"}


def test_topic_filter_is_or_across_multiple_topics():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=["topic:cholesterol", "topic:tmao"])
    ids = {n.id for n in nodes} - {"__question__"}
    assert ids == {"leaf-cholesterol", "leaf-tmao", "root-a", "root-b"}


def test_no_topic_filter_shows_everything():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, topic_filter=None)
    ids = {n.id for n in nodes} - {"__question__"}
    assert ids == set(graph.claims)


def test_topic_filter_combines_with_crux_filter_but_roots_still_show():
    # a claim matching the topic but not a crux is excluded once both
    # filters are active -- filters intersect, they don't OR across kinds --
    # but roots are exempt from every filter, so they remain.
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, show_only_cruxes=True, topic_filter=["topic:cholesterol"])
    ids = {n.id for n in nodes} - {"__question__"}
    assert ids == {"root-a", "root-b"}


def test_roots_survive_a_non_matching_search():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, search_query="text that matches nothing")
    ids = {n.id for n in nodes} - {"__question__"}
    assert ids == {"root-a", "root-b"}


def test_question_node_always_present_above_roots_and_survives_filters():
    graph = _graph()
    nodes, _edges = graph_view.build_elements(graph, show_only_cruxes=True, topic_filter=["topic:cholesterol"])
    question_nodes = [n for n in nodes if n.id == "__question__"]
    assert len(question_nodes) == 1
    node = question_nodes[0]
    assert node.shape == "text"
    assert node.y < -(graph_view.ROOT_NODE_WIDTH / 2)  # clears the root's top edge, which sits at y=0
    assert node.x == 0


def test_question_node_y_grows_with_wrapped_line_count():
    # a longer question wraps to more lines and needs a text block that
    # extends further down -- its y must move further up (more negative)
    # to keep the same minimum gap above the roots, not stay fixed.
    short = Graph(case_id="s", question="Short?", claims={"root-a": _claim("root-a")}, edges=[], sources={})
    long = Graph(
        case_id="l",
        question="A genuinely much longer question that will wrap across several lines " * 2,
        claims={"root-a": _claim("root-a")},
        edges=[],
        sources={},
    )
    short_y = next(n.y for n in graph_view.build_elements(short)[0] if n.id == "__question__")
    long_y = next(n.y for n in graph_view.build_elements(long)[0] if n.id == "__question__")
    assert long_y < short_y

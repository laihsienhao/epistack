from datetime import date

from src.loader import Graph, load_case
from src.models import Claim, Edge
from src.research_priorities import research_priorities


def _claim(id_, tags=None, explanation=None):
    return Claim(
        id=id_,
        case="synthetic",
        text=id_,
        label=id_,
        tags=tags or [],
        explanation=explanation,
        author="tester",
        created=date(2026, 7, 13),
    )


def _edge(id_, from_, to, relation="supports"):
    return Edge(id=id_, relation=relation, from_=from_, to=to, author="tester", created=date(2026, 7, 13))


def test_research_priorities_on_eggs_case_resurfaces_the_hidden_double_crux():
    graph = load_case("eggs")
    priorities = research_priorities(graph)
    top = priorities[0]
    assert top["claim_id"] == "cholesterol-causal-effect-contested"
    assert set(top["reference_points"]) == {"eggs-fine-in-moderation", "eggs-should-be-limited"}


def test_contextual_tagged_crux_is_excluded():
    claims = {
        "root": _claim("root"),
        "crux": _claim("crux", tags=["contextual"]),
    }
    edges = [_edge("e1", "crux", "root", "depends_on")]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    assert research_priorities(graph) == []


def test_ranked_by_reference_point_count_then_impact():
    claims = {
        "root-a": _claim("root-a"),
        "root-b": _claim("root-b"),
        "double-crux": _claim("double-crux"),
        "single-crux": _claim("single-crux"),
        "feeder-1": _claim("feeder-1"),
        "feeder-2": _claim("feeder-2"),
    }
    edges = [
        _edge("e1", "double-crux", "root-a", "depends_on"),
        _edge("e2", "double-crux", "root-b", "depends_on"),
        _edge("e3", "single-crux", "root-a", "depends_on"),
        # give single-crux a bigger upstream subtree than double-crux, to
        # confirm reference-point count still wins the primary sort
        _edge("e4", "feeder-1", "single-crux", "supports"),
        _edge("e5", "feeder-2", "single-crux", "supports"),
    ]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    priorities = research_priorities(graph)
    ids = [p["claim_id"] for p in priorities]
    assert ids.index("double-crux") < ids.index("single-crux")


def test_explanation_carried_through_for_display():
    claims = {
        "root": _claim("root"),
        "crux": _claim("crux", explanation="A longer RCT would settle this."),
    }
    edges = [_edge("e1", "crux", "root", "depends_on")]
    graph = Graph(case_id="synthetic", question="Test question?", claims=claims, edges=edges, sources={})
    priorities = research_priorities(graph)
    assert graph.claims[priorities[0]["claim_id"]].explanation == "A longer RCT would settle this."

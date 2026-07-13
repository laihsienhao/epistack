import yaml

from src.loader import compute_depths, list_cases, load_case, reachable_roots
from src.validate import validate_case


def _write_case(base_dir, case_id, claims, edges, sources):
    case_dir = base_dir / case_id
    case_dir.mkdir(parents=True)
    (case_dir / "claims.yaml").write_text(yaml.safe_dump(claims))
    (case_dir / "edges.yaml").write_text(yaml.safe_dump(edges))
    (case_dir / "sources.yaml").write_text(yaml.safe_dump(sources))
    return case_dir


def _minimal_claim(id_, **overrides):
    base = {
        "id": id_,
        "case": "synthetic",
        "text": f"claim {id_}",
        "label": f"claim {id_}",
        "author": "tester",
        "created": "2026-07-13",
    }
    base.update(overrides)
    return base


def _minimal_edge(id_, from_, to, relation="supports", **overrides):
    base = {
        "id": id_,
        "relation": relation,
        "from": from_,
        "to": to,
        "author": "tester",
        "created": "2026-07-13",
    }
    base.update(overrides)
    return base


def test_load_toy_case():
    graph = load_case("toy")
    assert graph.case_id == "toy"
    assert set(graph.roots()) == {"coffee-is-healthy", "coffee-is-harmful"}
    assert "coffee-contains-caffeine" in graph.claims
    assert len(graph.edges) == 7


def test_outgoing_incoming():
    graph = load_case("toy")
    outgoing = graph.outgoing("coffee-contains-caffeine")
    assert {e.to for e in outgoing} == {
        "caffeine-improves-alertness",
        "caffeine-raises-blood-pressure-acutely",
    }
    incoming = graph.incoming("coffee-is-healthy")
    assert {e.from_ for e in incoming} == {
        "caffeine-improves-alertness",
        "long-term-mortality-data-favor-coffee",
        "coffee-net-mortality-effect-contested",
    }


def test_list_cases_includes_toy():
    assert "toy" in list_cases()


def test_compute_depths_roots_are_zero_and_increase_outward():
    graph = load_case("toy")
    depths = compute_depths(graph)
    assert depths["coffee-is-healthy"] == 0
    assert depths["coffee-is-harmful"] == 0
    assert depths["caffeine-improves-alertness"] == 1
    # reachable via two different-length paths (through alertness AND directly
    # unreachable) -- coffee-contains-caffeine is two supports-hops from either root
    assert depths["coffee-contains-caffeine"] == 2


def test_reachable_roots_flags_shared_claims():
    graph = load_case("toy")
    shared = reachable_roots(graph)
    assert shared["coffee-contains-caffeine"] == {"coffee-is-healthy", "coffee-is-harmful"}
    assert shared["coffee-net-mortality-effect-contested"] == {
        "coffee-is-healthy",
        "coffee-is-harmful",
    }
    # not shared -- only feeds the health thesis
    assert shared["caffeine-improves-alertness"] == {"coffee-is-healthy"}


def test_validate_toy_case_is_clean():
    assert validate_case("toy") == []


def test_validate_detects_dangling_reference(tmp_path):
    _write_case(
        tmp_path,
        "bad-dangling",
        claims=[_minimal_claim("a")],
        edges=[_minimal_edge("e1", "a", "missing-claim")],
        sources=[],
    )
    errors = validate_case("bad-dangling", base_dir=tmp_path)
    assert any("dangling 'to' claim id missing-claim" in e for e in errors)


def test_validate_detects_duplicate_claim_id(tmp_path):
    _write_case(
        tmp_path,
        "bad-dup",
        claims=[_minimal_claim("a"), _minimal_claim("a")],
        edges=[],
        sources=[],
    )
    errors = validate_case("bad-dup", base_dir=tmp_path)
    assert any("duplicate claim id: a" in e for e in errors)


def test_validate_detects_dangling_source_reference(tmp_path):
    _write_case(
        tmp_path,
        "bad-source-ref",
        claims=[_minimal_claim("a", sources=["missing-source"])],
        edges=[],
        sources=[],
    )
    errors = validate_case("bad-source-ref", base_dir=tmp_path)
    assert any("dangling source id missing-source" in e for e in errors)


def test_validate_detects_cycle(tmp_path):
    _write_case(
        tmp_path,
        "bad-cycle",
        claims=[_minimal_claim("a"), _minimal_claim("b")],
        edges=[
            _minimal_edge("e1", "a", "b"),
            _minimal_edge("e2", "b", "a"),
        ],
        sources=[],
    )
    errors = validate_case("bad-cycle", base_dir=tmp_path)
    assert any("cycle detected" in e for e in errors)

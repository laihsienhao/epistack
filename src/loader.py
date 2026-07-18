from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import Case, Claim, Edge, Source

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"


@dataclass
class Graph:
    case_id: str
    question: str
    claims: dict[str, Claim]
    edges: list[Edge]
    sources: dict[str, Source]
    _outgoing_cache: dict[str, list[Edge]] = field(default_factory=dict, repr=False, init=False)
    _incoming_cache: dict[str, list[Edge]] = field(default_factory=dict, repr=False, init=False)

    def __post_init__(self) -> None:
        for edge in self.edges:
            self._outgoing_cache.setdefault(edge.from_, []).append(edge)
            self._incoming_cache.setdefault(edge.to, []).append(edge)

    def outgoing(self, claim_id: str) -> list[Edge]:
        return self._outgoing_cache.get(claim_id, [])

    def incoming(self, claim_id: str) -> list[Edge]:
        return self._incoming_cache.get(claim_id, [])

    def roots(self) -> list[str]:
        """Claims with no outgoing edges — the graph's 'schools of thought'."""
        return [cid for cid in self.claims if not self.outgoing(cid)]

    def resolve_sources(self, source_ids: list[str]) -> list[Source]:
        return [self.sources[sid] for sid in source_ids if sid in self.sources]


def _load_yaml(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        data = yaml.safe_load(f)
    return data or []


def _load_yaml_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        data = yaml.safe_load(f)
    return data or {}


def load_case(case_id: str, base_dir: Path | None = None) -> Graph:
    case_dir = (base_dir or DATA_DIR) / case_id
    case_meta = Case(**_load_yaml_dict(case_dir / "case.yaml"))
    claims_raw = _load_yaml(case_dir / "claims.yaml")
    edges_raw = _load_yaml(case_dir / "edges.yaml")
    sources_raw = _load_yaml(case_dir / "sources.yaml")

    claims: dict[str, Claim] = {}
    for raw in claims_raw:
        claim = Claim(**raw)
        if claim.id in claims:
            raise ValueError(f"duplicate claim id: {claim.id}")
        claims[claim.id] = claim

    sources: dict[str, Source] = {}
    for raw in sources_raw:
        source = Source(**raw)
        if source.id in sources:
            raise ValueError(f"duplicate source id: {source.id}")
        sources[source.id] = source

    edges: list[Edge] = []
    seen_edge_ids: set[str] = set()
    for raw in edges_raw:
        edge = Edge(**raw)
        if edge.id in seen_edge_ids:
            raise ValueError(f"duplicate edge id: {edge.id}")
        seen_edge_ids.add(edge.id)
        edges.append(edge)

    return Graph(case_id=case_id, question=case_meta.question, claims=claims, edges=edges, sources=sources)


def compute_depths(graph: Graph) -> dict[str, int]:
    """Longest-path depth from each claim to a root, following any outgoing edge.

    Roots (no outgoing edges) are depth 0; a claim's depth is one more than
    the deepest claim it points into. This is the sole source of vertical
    position in the UI — never stored, always derived. Assumes the graph is
    acyclic (see validate.py); a cycle raises rather than looping forever.
    """
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(claim_id: str) -> int:
        if claim_id in memo:
            return memo[claim_id]
        if claim_id in visiting:
            raise ValueError(f"cycle detected while computing depth at {claim_id}")
        visiting.add(claim_id)
        outgoing = graph.outgoing(claim_id)
        depth = 0 if not outgoing else 1 + max(visit(edge.to) for edge in outgoing)
        visiting.discard(claim_id)
        memo[claim_id] = depth
        return depth

    for claim_id in graph.claims:
        visit(claim_id)
    return memo


def reachable_roots(graph: Graph) -> dict[str, set[str]]:
    """Map claim id -> set of root ids reachable by following any outgoing edge.

    A claim reachable from >=2 roots is a shared ground-truth candidate — no
    stored field, just a traversal over the edges already in the graph.
    """
    roots = set(graph.roots())
    memo: dict[str, set[str]] = {}

    def visit(claim_id: str) -> set[str]:
        if claim_id in memo:
            return memo[claim_id]
        if claim_id in roots:
            memo[claim_id] = {claim_id}
            return memo[claim_id]
        result: set[str] = set()
        for edge in graph.outgoing(claim_id):
            result |= visit(edge.to)
        memo[claim_id] = result
        return result

    for claim_id in graph.claims:
        visit(claim_id)
    return memo


def list_cases(base_dir: Path | None = None) -> list[str]:
    base = base_dir or DATA_DIR
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())

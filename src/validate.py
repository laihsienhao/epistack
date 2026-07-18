from pathlib import Path

from pydantic import ValidationError

from .loader import DATA_DIR, _load_yaml, _load_yaml_dict
from .models import Case, Claim, Edge, Source


def validate_case(case_id: str, base_dir: Path | None = None) -> list[str]:
    """Return a list of validation error messages (empty if the case is valid).

    Checks schema conformance, duplicate ids, dangling references, and DAG
    cycles (the derived-hierarchy layout requires the claim graph to be
    acyclic).
    """
    errors: list[str] = []
    case_dir = (base_dir or DATA_DIR) / case_id

    try:
        Case(**_load_yaml_dict(case_dir / "case.yaml"))
    except ValidationError as e:
        errors.append(f"case.yaml: schema error: {e}")

    claims_raw = _load_yaml(case_dir / "claims.yaml")
    edges_raw = _load_yaml(case_dir / "edges.yaml")
    sources_raw = _load_yaml(case_dir / "sources.yaml")

    claims: dict[str, Claim] = {}
    for raw in claims_raw:
        try:
            claim = Claim(**raw)
        except ValidationError as e:
            errors.append(f"claim {raw.get('id', '?')}: schema error: {e}")
            continue
        if claim.id in claims:
            errors.append(f"duplicate claim id: {claim.id}")
        claims[claim.id] = claim

    sources: dict[str, Source] = {}
    for raw in sources_raw:
        try:
            source = Source(**raw)
        except ValidationError as e:
            errors.append(f"source {raw.get('id', '?')}: schema error: {e}")
            continue
        if source.id in sources:
            errors.append(f"duplicate source id: {source.id}")
        sources[source.id] = source

    edges: list[Edge] = []
    seen_edge_ids: set[str] = set()
    for raw in edges_raw:
        try:
            edge = Edge(**raw)
        except ValidationError as e:
            errors.append(f"edge {raw.get('id', '?')}: schema error: {e}")
            continue
        if edge.id in seen_edge_ids:
            errors.append(f"duplicate edge id: {edge.id}")
        seen_edge_ids.add(edge.id)
        edges.append(edge)

    for edge in edges:
        if edge.from_ not in claims:
            errors.append(f"edge {edge.id}: dangling 'from' claim id {edge.from_}")
        if edge.to not in claims:
            errors.append(f"edge {edge.id}: dangling 'to' claim id {edge.to}")
        for src_id in edge.provenance:
            if src_id not in sources:
                errors.append(f"edge {edge.id}: dangling provenance source id {src_id}")

    for claim in claims.values():
        for src_id in claim.sources:
            if src_id not in sources:
                errors.append(f"claim {claim.id}: dangling source id {src_id}")

    errors.extend(_find_cycles(claims, edges))
    return errors


def _find_cycles(claims: dict[str, Claim], edges: list[Edge]) -> list[str]:
    adjacency: dict[str, list[str]] = {cid: [] for cid in claims}
    for edge in edges:
        if edge.from_ in adjacency and edge.to in adjacency:
            adjacency[edge.from_].append(edge.to)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in claims}
    found: list[str] = []
    reported_cycles: set[frozenset] = set()

    def visit(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in adjacency.get(node, []):
            if color[neighbor] == GRAY:
                cycle_nodes = path[path.index(neighbor):] + [neighbor]
                key = frozenset(cycle_nodes)
                if key not in reported_cycles:
                    reported_cycles.add(key)
                    found.append(f"cycle detected: {' -> '.join(cycle_nodes)}")
            elif color[neighbor] == WHITE:
                visit(neighbor, path)
        path.pop()
        color[node] = BLACK

    for cid in claims:
        if color[cid] == WHITE:
            visit(cid, [])

    return found

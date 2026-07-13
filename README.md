# Epistemic Claim Graph

An interactive tool for mapping contested topics as a **claim graph** — built for the
[Future of Life Foundation Epistemic Case Study Competition](https://flf.org/epistack-competition).

It targets the **Structure** layer of the competition's "epistemic stack": turning a
messy, multi-source debate into a reusable, extensible artifact that shows *what's
actually being argued*, *how the argument is structured*, and — the standout
feature — *which specific claims would actually resolve the disagreement if settled*.

## The model

- **Nodes are claims** — single, crisp assertions, not sources or people.
- **Edges are logical relations** — `supports` ("this is evidence for the claim it
  points to") or `depends_on` ("the claim it points to can only hold if this one
  does"). There is deliberately no `contradicts` relation.
- **Disagreement is structural, not an edge.** When a topic has competing positions,
  each position is its own root claim (a node with no outgoing edges) — there's no
  edge connecting rival theses. Two diverging trees *are* the disagreement.
- **Hierarchy is derived, never stored.** A claim's vertical position is its depth in
  the DAG, computed from edge direction. No manual "level" field, no layout
  coordinates in the data — the graph itself stays portable.
- **Shared ground-truths fall out of the graph for free.** A claim reachable from
  more than one root is, by construction, something both sides rely on.
- **Cruxes are derived too.** A claim is a *crux* for a root if there's a path of
  `depends_on` edges (never `supports`) from it up to that root — i.e. falsifying it
  breaks a necessary condition, not just weakens an argument. A claim that's a crux
  for **two or more** roots simultaneously is a **double crux**: the rare, high-value
  case where a single unresolved question would move more than one side. The app
  highlights these directly on the graph and in a dedicated Cruxes panel — this is
  close to the single most useful thing a debate-navigation tool can say: *here is
  the specific question that would actually resolve this*.

None of the above needs a schema field beyond `relation: supports | depends_on` —
hierarchy, shared ground-truths, and cruxes are all graph queries over that one
distinction, computed at render time (`src/loader.py`, `src/crux.py`).

## Case studies

- **`eggs`** — is dietary cholesterol from eggs something to limit, or fine in
  moderation? Chosen as the starting case for its small, tractable evidence base.
- **`toy`** — a small synthetic example (coffee and mortality) used to exercise and
  test the pipeline's mechanics independent of any real research question.

Adding a new case study requires **zero application code changes** — just new
`claims.yaml` / `edges.yaml` / `sources.yaml` files under `data/cases/<case_id>/`.
See [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md).

## Running it

```bash
git clone <repo-url> && cd epistemology
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

Opens at `http://localhost:8501`. Use the sidebar to switch cases, filter by tag or
search text, or isolate cruxes; click a node to see its full explanation, resolved
references, and in/out edges; use the Contribute tab to draft a new claim or edge and
export it as YAML to submit as a PR.

## Validating a case

```bash
python -m src.main validate <case_id>
```

Checks schema conformance, duplicate ids, dangling references, and DAG cycles (the
hierarchy layout requires the graph to be acyclic).

```bash
pytest tests/
```

## Project layout

```
data/cases/<case_id>/{claims,edges,sources}.yaml   # the portable artifact itself
schema/*.schema.json                               # JSON Schema for each YAML shape
src/models.py                                      # pydantic Claim/Edge/Source
src/loader.py                                       # load_case, depth/reachability helpers
src/validate.py                                     # referential integrity + cycle detection
src/crux.py                                          # crux / double-crux detection
app/                                                  # Streamlit UI
```

## License

Code is MIT-licensed (`LICENSE`). The claim-graph data under `data/` is licensed
separately under CC-BY 4.0 (`data/LICENSE`) — fork it, extend it, merge it, as long
as you credit the source.

# Epistemic Claim Graph

An interactive tool for mapping contested topics as a **claim graph**, built for the
[Future of Life Foundation Epistemic Case Study Competition](https://flf.org/epistack-competition).

The core idea: turn a messy, multi-source debate into a structured, extensible
artifact that shows what is being argued, how the argument is built, and
which specific claims would resolve the disagreement if they were settled.

Checked against the competition's own three-layer taxonomy (Ingestion, Structure,
Assessment), the project's primary focus is Structure, but several features land
in Ingestion and Assessment too. See ["Where this fits in the stack"](#where-this-fits-in-the-stack)
below for the full mapping.

## The model

- **Nodes are claims.** Single, precise assertions, not sources or people.
- **Edges are logical relations.** `supports` ("this is evidence for the claim it
  points to") or `depends_on` ("the claim it points to can only hold if this one
  does"). There is no `contradicts` relation.
- **Disagreement is structural, not an edge.** When a topic has competing positions,
  each position is its own root claim (a node with no outgoing edges). There is no
  edge connecting rival theses; two diverging trees are the disagreement.
- **Hierarchy is derived, never stored.** A claim's position in the hierarchy is its
  depth in the graph, computed from edge direction. There is no manual "level"
  field and no layout coordinates in the data, so the graph itself stays portable.
- **Shared ground truths fall out of the graph for free.** A claim reachable from
  more than one root is, by construction, something both sides rely on.
- **Cruxes are derived too.** A claim is a crux for a root if there is a path of
  `depends_on` edges (never `supports`) from it up to that root: falsifying it
  breaks a necessary condition, not just weakens an argument. A claim that is a
  crux for two or more roots at once is a **double crux**: the case where a single
  unresolved question would move more than one side. The app highlights these on
  the graph and in a dedicated Cruxes panel, which is close to the single most
  useful thing a debate-navigation tool can surface: the specific question that
  would resolve the disagreement.

None of this needs a schema field beyond `relation: supports | depends_on`.
Hierarchy, shared ground truths, and cruxes are all graph queries over that one
distinction, computed at render time (`src/loader.py`, `src/crux.py`).

A further extension, `src/research_priorities.py`, generalizes crux detection
beyond root claims to any "sub-thesis" node with two or more incoming edges. This
matters because crux status is relative to whatever the current reference points
are: broadening a thesis to rest on several independently sufficient pillars can
make a load-bearing open question disappear from the root-level view even though
it is exactly as load-bearing as before within its own branch. The Research
Priorities panel restores visibility into those questions and ranks them by how
much of the graph's structure routes through them, giving a direct answer to
"which open question matters most."

Two further Structure-layer pieces derive from a `topic:<name>` tag on claims
(`src/discourse.py`): a **Coverage** tab showing which sub-questions each side
engages with, distinguishing topics both sides address (an explicit difference of
emphasis, even when they reach opposite conclusions) from topics only one side has
built out, plus claim and source counts per side per topic, so an implicit
emphasis imbalance is visible too, not just presence or absence. A topic filter in
the graph toolbar navigates by sub-question the same way search and the crux
filter navigate by text and load-bearing status.

## Where this fits in the stack

- **Structure** is the primary focus: inference structure (`supports`/`depends_on`,
  derived hierarchy, shared ground truths) and discourse structure (the Coverage
  tab and topic tags described above).
- **Assessment.** The competition's own taxonomy places "identifying cruxes" under
  Assessment, not Structure, so crux and double-crux detection, this project's
  flagship feature, belongs here too. So does the Coverage tab's one-sided-topic
  view ("surfacing missing sources or perspectives" is explicitly an Assessment
  concern); the `contested`/`contextual` tag distinction (a genuine open dispute
  versus an apparent conflict that resolves once the scenario is specified,
  matching "distinguishing settled debates from performed ones"); the graph's
  dashed-versus-solid edge rendering (an editorial judgment call versus a claim
  backed by a specific citation); and the shared-authorship flag described next.
- **Ingestion.** Every source carries full provenance metadata (type, authors,
  year, venue, url), plus a required `funding` classification and optional
  `bias_note`, verified against each source's disclosed funding or conflict-of-
  interest statement rather than inferred from venue or author
  (`src/models.py`, `app/detail_panel.py`). The claim-detail popup's Evidence tab
  also flags when two of a claim's own sources share an author surname
  (`src/ingestion.py`): a duplicate/overlap check at the metadata level that
  doubles as the Assessment-layer signal above, since it flags correlated
  evidence that might otherwise be treated as independent. Not built: duplicate
  claim detection across sources, and any live resource-search capability. See
  [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full account of what is
  and is not covered, and where the approach is still weak.

## Case studies

Every case states its own neutral framing question in `case.yaml`, kept separate
from the root claims themselves: a root is one side's answer, not the question
both sides are answering.

The competition supplies three official case studies, deliberately spanning three
different shapes (mundane-but-contested, confident-answer-with-complex-evidence,
curated debate). All three have real, sourced content here, plus a small
synthetic case used for testing.

| Case | Question | Shape | Claims / Edges / Sources |
|---|---|---|---|
| `eggs` | What are the health impacts of eggs as a human food source? | Mundane but contested: a roughly symmetric debate across several independent mechanisms (cholesterol, TMAO, diabetes risk, saturated fat, cooking method, food safety, cancer risk, and more) | 21 / 23 / 47 |
| `lhc-black-holes` | Does the Large Hadron Collider pose a genuine risk of creating dangerous black holes? | Confident answer with complex evidence: an overwhelming, institutionally endorsed scientific consensus against a small number of named, individually rebutted critics | 17 / 16 / 24 |
| `covid-19-origins` | How did SARS-CoV-2 first enter the human population? | Curated debate: the most evenly contested of the three, with natural zoonotic spillover as the dominant peer-reviewed position against a research-related origin taken seriously by several split US intelligence assessments | 19 / 22 / 41 |
| `toy` | Is habitual moderate coffee consumption beneficial or harmful for long-term health? | Synthetic example, used only to exercise the pipeline's mechanics | 7 / 7 / 2 |

Each case's crux structure differs in an informative way. `eggs` broadened its
original two theses into umbrella roots resting on several independently
sufficient pillars, which means the original cholesterol crux no longer registers
at the top level (it still does at the sub-thesis level, via the Research
Priorities panel). `lhc-black-holes` has a single crux on the dissenting side.
`covid-19-origins` has a single crux on the consensus-leaning side, since pure
natural spillover and deliberate engineering are mutually exclusive while a
research-accident origin does not require any single finding the same way. None
of this was designed in advance; it is what the crux algorithm returns once the
graph is built, and it is checked directly rather than assumed.

Adding a new case requires **zero application code changes**: only new
`case.yaml` / `claims.yaml` / `edges.yaml` / `sources.yaml` files under
`data/cases/<case_id>/`. See [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md)
for the full authoring guide. This has now been demonstrated on all three of the
competition's own official cases, not asserted once.

## Running it

```bash
git clone <repo-url> && cd epistemology
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

Opens at `http://localhost:8501`. Use the sidebar to switch cases, filter by
topic or search text, or isolate cruxes; click a node to see its full
explanation, resolved references, and incoming/outgoing edges; use the
Contribute tab to draft a new claim, edge, or source and export it as YAML to
submit as a pull request.

## Validating a case

```bash
python -m src.main validate <case_id>
```

Checks schema conformance, duplicate ids, dangling references, and cycles (the
hierarchy layout requires the graph to be acyclic).

```bash
pytest tests/
```

## Project layout

```
data/cases/<case_id>/{case,claims,edges,sources}.yaml   # the portable artifact itself
schema/*.schema.json                                    # JSON Schema for each YAML shape
src/models.py                                           # pydantic Case/Claim/Edge/Source
src/loader.py                                           # load_case, depth/reachability helpers
src/validate.py                                         # referential integrity + cycle detection
src/crux.py                                             # crux / double-crux detection
src/research_priorities.py                              # sub-thesis-aware crux ranking
src/discourse.py                                        # topic coverage/emphasis (Coverage tab)
src/ingestion.py                                        # shared-authorship / correlated-evidence flag
app/                                                     # Streamlit UI
```

## License

Code is MIT-licensed (`LICENSE`). The claim-graph data under `data/` is licensed
separately under CC-BY 4.0 (`data/LICENSE`): fork it, extend it, merge it, as
long as you credit the source.

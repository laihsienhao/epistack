# Epistemic Claim Graph

An interactive tool for mapping contested topics as a **claim graph** — built for the
[Future of Life Foundation Epistemic Case Study Competition](https://flf.org/epistack-competition).

It primarily targets the **Structure** layer of the competition's "epistemic stack":
turning a messy, multi-source debate into a reusable, extensible artifact that shows
*what's actually being argued*, *how the argument is structured*, and — the standout
feature — *which specific claims would actually resolve the disagreement if settled*.

Checked against the competition's own three-layer taxonomy (**Ingestion** / **Structure**
/ **Assessment**), the feature set actually spans more than Structure alone — see
["Beyond Structure"](#beyond-structure--ingestion--assessment) below.

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

Two further Structure-layer pieces derive from a `topic:<name>` tag on claims
(`src/discourse.py`): a **Coverage** tab showing which sub-questions each side
actually engages with — distinguishing topics both sides address (an *explicit*
difference of emphasis, even when they reach opposite conclusions) from topics only
one side has built out — plus claim/source counts per side per topic, so an
*implicit* emphasis imbalance (both sides technically cover a topic, one far more than
the other) is visible too, not just binary presence/absence. A topic filter in the
graph toolbar navigates by sub-question the same way search and the crux filter
already navigate by text and load-bearing status.

## Beyond Structure — Ingestion & Assessment

The competition's site places some of this project's work outside Structure:

- **Assessment.** The competition's own taxonomy places "identifying cruxes" under
  *Assessment*, not Structure — so crux/double-crux detection, this project's
  flagship feature, is already an Assessment-layer contribution. So is the Coverage
  tab's one-sided-topic view ("surfacing missing sources or perspectives" is
  explicitly Assessment); the `contested`/`contextual` tag distinction (a genuine open
  dispute vs. an apparent conflict that resolves once you specify the scenario —
  "distinguishing settled debates from performed ones"); the graph's dashed-vs-solid
  edge rendering (unsourced editorial judgment vs. a claim backed by a specific
  citation — a structural signal toward evidential-vs-rhetorical distinction); and the
  claim-detail popup's shared-authorship flag (below) — "flagging correlated evidence
  treated as independent," close to verbatim.
- **Ingestion.** Every source carries full provenance metadata (type, authors, year,
  venue, url), plus a required `funding` classification and optional `bias_note` —
  verified against each real source's actual disclosed funding/COI statement, not
  inferred from venue or author (`src/models.py`, `app/detail_panel.py`). The
  claim-detail popup's Evidence tab also flags when two of a claim's own sources list
  an author surname in common (`src/ingestion.py`) — a duplicate/overlap check at the
  metadata level that doubles as the Assessment-layer signal above. Not built: duplicate
  *claim* detection across sources, and any live resource-search capability — named as
  open in `docs/METHODOLOGY.md`, not attempted here.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full account, including
where this is still weak.

## Case studies

Every case states its own neutral framing question (`case.yaml`), separate from the
root claims themselves — a root is one side's *answer*, not the question both sides
are answering.

- **`eggs`** — "What are the health impacts of eggs as a human food source?" Matches
  the competition's own "eggs as food" official case study.
- **`lhc-black-holes`** — "Does the Large Hadron Collider pose a genuine risk of
  creating dangerous black holes?" Matches the competition's own "LHC black hole
  risk" official case study — a structurally different shape than `eggs`: not a
  roughly-symmetric rival-schools-of-thought debate, but an overwhelming,
  institutionally-endorsed scientific consensus against a handful of named,
  individually-rebutted critics. 24 real sources, individually funding-verified.
- **`covid-19-origins`** — "How did SARS-CoV-2 first enter the human population?"
  Matches the competition's own "COVID-19 origins" official case study — the
  "curated debate" shape, and the most evenly-contested of the three: natural
  zoonotic spillover (the dominant peer-reviewed virology position) against a
  plausible, unexcluded research-related origin (taken seriously by several split
  US intelligence assessments). 41 real sources, individually funding-verified,
  including several with disclosed industry/advocacy ties on both sides of the
  debate, surfaced rather than smoothed over. Crux detection finds a genuine
  single-root crux here too — but, unlike `lhc-black-holes` (crux on the
  dissenting side), it lands on the *consensus-leaning* side: the natural-origin
  root structurally depends on the genome showing no engineering signature,
  since deliberate engineering and pure natural spillover are mutually exclusive,
  while the lab-related-origin root doesn't depend on any single claim the same
  way (a research-accident scenario doesn't require engineering at all) — a third
  distinct structural signature, found by direct computation, not designed in
  advance.
- **`toy`** — "Is habitual moderate coffee consumption beneficial or harmful for
  long-term health?" A small synthetic example used to exercise and test the
  pipeline's mechanics independent of any real research question.

The competition provides three official case studies — **eggs**, **LHC black hole
risk**, and **COVID-19 origins** (all three now covered above) — deliberately
spanning three different shapes (mundane-but-contested /
confident-answer-with-complex-evidence / curated debate). Adding a case requires
**zero application code changes** (just new `case.yaml` / `claims.yaml` /
`edges.yaml` / `sources.yaml` files under `data/cases/<case_id>/`, see
[`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md)) — demonstrated on all
three of the competition's own cases now, not just asserted once.

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
data/cases/<case_id>/{case,claims,edges,sources}.yaml   # the portable artifact itself
schema/*.schema.json                               # JSON Schema for each YAML shape
src/models.py                                      # pydantic Case/Claim/Edge/Source
src/loader.py                                       # load_case, depth/reachability helpers
src/validate.py                                     # referential integrity + cycle detection
src/crux.py                                          # crux / double-crux detection
src/discourse.py                                     # topic coverage/emphasis (Coverage tab)
src/ingestion.py                                     # shared-authorship / correlated-evidence flag
app/                                                  # Streamlit UI
```

## License

Code is MIT-licensed (`LICENSE`). The claim-graph data under `data/` is licensed
separately under CC-BY 4.0 (`data/LICENSE`) — fork it, extend it, merge it, as long
as you credit the source.

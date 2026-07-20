# Epistemic Claim Graph

An interactive tool for mapping contested topics as a **claim graph**, built for the
[Future of Life Foundation Epistemic Case Study Competition](https://flf.org/epistack-competition).

A disagreement worth taking seriously is rarely a disagreement about which facts
exist. What separates two informed people is which facts they weight
most heavily, how those facts connect into an argument, and which single claim,
if it turned out to be false, would change their mind. Prose discards exactly
that structure: a summary article can list the same evidence both sides cite,
but it has no way to show which piece of evidence is doing the real work, which
claims both sides already share without noticing, or which one question the
whole disagreement turns on.

This project has two parts, referred to together as the **framework**:

- **The Claim Graph**, a schema and set of derived views that represent a
  contested debate as claims (nodes) and logical relations between them
  (edges), so a reader can inspect the structure of a disagreement directly
  instead of reconstructing it from prose. This is the core contribution.
- **The Workflow**, a six-stage, AI-assisted process used to build every claim,
  edge, and source in this repository. It is what builds and verifies the graph
  in practice; see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full
  specification.

Building a debate this way does not settle it, and it does not adjudicate which
side is right. What it does is make the structure of the disagreement, common
ground, the single question the debate rests on, which parts are
backed by a citation rather than editorial judgment, a property of the graph
itself, computed from how the claims connect rather than asserted by whoever
built it.

Checked against the competition's own three-layer taxonomy (Ingestion, Structure,
Assessment), the project's primary focus is Structure, but several features land
in Ingestion and Assessment too. See ["Where this fits in the stack"](#where-this-fits-in-the-stack)
below for the full mapping.

## The Claim Graph

- **Nodes are claims.** Single, precise assertions, not sources or people. Each
  claim carries an evidentiary layer, the sources and references that support
  it, including each source's type, funding, and disclosed conflicts of
  interest.
- **Edges are logical relations.** `supports` (claim A supports claim B if B
  would still hold, perhaps more weakly, without A) or `depends_on` (claim A
  depends on claim B if A cannot hold without B). There is no `contradicts`
  relation.
- **Disagreement is structural, not an edge.** When a topic has competing
  positions, each position is its own root claim (a node with no outgoing
  edges). There is no edge connecting rival theses; two diverging trees are
  the disagreement. No claim has to "declare" a position up front; a claim's
  position falls out of which root's tree it is reachable from.
- **Hierarchy is derived, never stored.** A claim's position in the hierarchy is
  its depth in the graph, the longest path of edges from it to its root,
  computed from edge direction. There is no manual "level" field and no layout
  coordinates in the data, so the graph itself stays portable.
- **Shared ground truths fall out of the graph for free.** A claim reachable
  from more than one root is, by construction, something both sides rely on,
  a fact or mechanism neither side disputes, surfaced without manual curation.
- **Cruxes are derived too.** A claim is a crux for a root if there is a path
  of `depends_on` edges (never `supports`) from it up to that root: falsifying
  it breaks a necessary condition, not just weakens an argument. A claim that
  is a crux for two or more roots at once is a **double crux**: the case where
  a single unresolved question would move more than one side. The app
  highlights these on the graph and in a dedicated Cruxes panel, which is
  close to the single most useful thing a debate-navigation tool can surface:
  the specific question that would resolve the disagreement.

None of this needs a schema field beyond `relation: supports | depends_on`.
Hierarchy, shared ground truths, and cruxes are all graph queries over that one
distinction, computed at render time (`src/loader.py`, `src/crux.py`).

A further extension, `src/research_priorities.py`, generalizes crux detection
beyond root claims to any "sub-thesis" node with two or more incoming edges.
This matters because crux status is relative to whatever the current reference
points are: broadening a thesis to rest on several independently sufficient
pillars can make a load-bearing open question disappear from the root-level
view even though it is exactly as load-bearing as before within its own
branch. The Research Priorities panel restores visibility into those questions
and ranks them by how much of the graph's structure routes through them,
giving a direct answer to "which open question matters most."

Two further Structure-layer pieces derive from a `topic:<name>` tag on claims
(`src/discourse.py`): a **Coverage** tab showing which sub-questions each side
engages with, distinguishing topics both sides address (an explicit difference
of emphasis, even when they reach opposite conclusions) from topics only one
side has built out, plus claim and source counts per side per topic, so an
implicit emphasis imbalance is visible too, not just presence or absence. A
topic filter in the graph toolbar navigates by sub-question the same way
search and the crux filter navigate by text and load-bearing status.

The graph structure itself functions independently of AI tools, the same way
Wikipedia's contribution model does not require AI to operate. AI is what
makes building and maintaining a graph at any real scale practical; see the
next section.

## The Workflow

Every claim, edge, and source in this repository was built through the same
six-stage, AI-assisted process:

1. **Source discovery.** Given a sub-question, identify candidate peer-reviewed
   sources.
2. **Source verification.** Confirm each candidate is real by fetching the
   actual paper or record and extracting structured metadata. A source that
   cannot be verified as real is rejected outright.
3. **Funding and conflict-of-interest verification.** Check each verified
   source's disclosed funding or conflict-of-interest statement and classify
   it; write a `bias_note` only when something concrete is disclosed.
4. **Claim and edge authoring.** Draft node labels, claims, explanations, and
   tags, then decide each edge's relation. Deciding `supports` versus
   `depends_on` is an interpretive judgment call left to a human, since it sits
   directly upstream of crux detection; an AI agent can flag likely
   disagreements for a reviewer, but does not decide alone.
5. **Structural validation.** Mechanical and fully automated: schema
   conformance, referential integrity, acyclicity.
6. **Derived-view sanity check.** Re-run the derived views (cruxes, topic
   coverage, research priorities, shared authorship) against the updated graph
   and check the outputs are sensible. Both real errors caught during this
   project's construction (a shared-authorship false positive, a
   funding-verification pass that copied text from the wrong page) were found
   this way, not by re-reading code.

A modified version of this same workflow, with manual source entry as the
first step in place of AI-driven discovery, is also how a human contributor
adds to an existing case without any AI assistance at all.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full specification,
including the explicit decision procedure behind each judgment call in stage 4,
and [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md) for the
concrete authoring conventions stage 4 follows.

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
| `lhc-black-holes` | Does the Large Hadron Collider pose a risk of creating synthetic black holes? | Confident answer with complex evidence: an overwhelming, institutionally endorsed scientific consensus against a small number of named, individually rebutted critics | 17 / 16 / 24 |
| `covid-19-origins` | What are the origins of COVID-19? | Curated debate: the most evenly contested of the three, with natural zoonotic spillover as the dominant peer-reviewed position against a research-related origin taken seriously by several split US intelligence assessments | 19 / 22 / 41 |
| `toy` | Is habitual moderate coffee consumption beneficial or harmful for long-term health? | Synthetic example, used only to exercise the workflow's mechanics | 7 / 7 / 2 |

Each case's crux structure differs in an informative way. `eggs` broadened its
original two theses into umbrella roots resting on several independently
sufficient pillars, which means the original cholesterol crux no longer registers
at the top level (it still does at the sub-thesis level, via the Research
Priorities panel). `lhc-black-holes` has a single crux on the dissenting side,
since its safety case rests on several independent arguments while the
dissenting position's relevance rests on one specific unresolved mechanism.
`covid-19-origins` has a single crux on the consensus-leaning side instead,
since pure natural spillover and deliberate genetic engineering are mutually
exclusive while a research-accident origin does not require any single finding
the same way. None of this was designed in advance; it is what the crux
algorithm returns once each graph is built, checked directly rather than
assumed.

The rendering layer generalizes the same way the crux algorithm does: the
unmodified layout algorithm that positions nodes by depth and side adapts
automatically to a lopsided split, `lhc-black-holes` has ten claims on one
side and four on the other, without anything in the layout code knowing in
advance that a case is asymmetric.

Adding a new case requires **zero application code changes**: only new
`case.yaml` / `claims.yaml` / `edges.yaml` / `sources.yaml` files under
`data/cases/<case_id>/`. See [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md)
for the full authoring guide. This has now been demonstrated on all three of the
competition's own official cases, not asserted once.

## Running it

The commands below are for running or developing your own copy of the code.
Contributing content to a case does not require any of this: see
[`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md), which happens
entirely through the Contribute tab on the platform itself, no clone, no
install, no file to manage.

```bash
git clone <repo-url> && cd epistemology
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

Opens at `http://localhost:8501`. Use the sidebar to switch cases, filter by
topic or search text, or isolate cruxes; click a node to see its full
explanation, resolved references, and incoming/outgoing edges; use the
Contribute tab to submit a new claim, edge, or source for review.

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

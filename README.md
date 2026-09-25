# Epistemic Claim Graph

An interactive tool for mapping contested topics as a **claim graph**, built for the [Future of Life Foundation Epistemic Case Study Competition](https://flf.org/epistack-competition).

A disagreement that is worth taking seriously is rarely a disagreement about facts alone. Rather, it implicitly concerns what facts different parties weigh most heavily, how these facts connect into an argument, and which claims are the most load-bearing. Yet prose discards precisely this structure: a summary article can list the same evidence both sides cite, but it has no way to show which piece of evidence is the most crucial, which claims are shared by different parties, or which claims are cruxes for the disagreement.

This project has two parts, referred to together as the **framework**:

- **The Claim Graph**, a schema and set of derived views that represent a contested debate as claims (nodes) and logical relations between them (edges), allowing a reader to inspect the structure of a disagreement directly instead of reconstructing it from prose.
- **The Workflow**, a six-stage, AI-assisted process used to build all claims, edges, and sources in this repository. It builds and verifies the graph in practice; see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full specification.

This tool builds and elucidates the structure of a disagreement as neutrally as possible for all parties, allowing them to identify common ground and cruxes.

Checked against the competition's own three-layer taxonomy (Ingestion, Structure, Assessment), the project's primary focus is Structure, but several features land in Ingestion and Assessment too. See ["Where this fits in the stack"](#where-this-fits-in-the-stack) below for the full mapping.

## The Claim Graph

- **Nodes are claims.** Each node is a single assertion, not a source or a person. A claim lists the sources behind it, with each source's type, funding, and any disclosed conflicts of interest.
- **Edges are logical relations**, of two kinds. Claim A `supports` claim B if B would still hold, perhaps more weakly, without A. Claim A `depends_on` claim B if A cannot hold without B. There is no `contradicts` relation.
- **Each position is a root.** A root is a claim with no outgoing edges. Rival positions are separate roots with no edge between them, and the disagreement is the two trees that grow beneath them. A claim belongs to whichever root(s) it can reach.
- **Hierarchy is computed.** A claim's level is the longest path from it to a root. The data stores no levels and no layout coordinates.
- **Shared ground truths are computed.** A claim reachable from more than one root is something both sides rely on.
- **Cruxes are computed.** A claim is a crux for a root if a path of `depends_on` edges (no `supports`) leads from it to that root, so falsifying it removes a necessary condition rather than weakening an argument. A crux for two or more roots is a **double crux**. The app highlights cruxes on the graph and lists them in the Cruxes panel.

All of this comes from the one `supports` / `depends_on` distinction and is computed at render time (`src/loader.py`, `src/crux.py`).

Crux status depends on which claims are treated as reference points. If a thesis rests on several independently sufficient pillars, no single open question is necessary for the whole thesis, so nothing shows up as a crux at the root level, even when a question is still necessary for one of the pillars. `src/research_priorities.py` also treats "sub-thesis" nodes (non-root claims with two or more incoming edges) as reference points. The Research Priorities panel lists the resulting questions, ranked by how much of the graph depends on them.

Claims can also carry `topic:<name>` tags (`src/discourse.py`). The **Coverage** tab uses them to show which sub-questions each side addresses, which topics both sides address (often reaching opposite conclusions), which only one side addresses, and how many claims and sources each side has per topic. The graph toolbar can filter by topic, alongside text search and the crux filter.

The graph itself does not need AI to work, in the same way Wikipedia does not. AI is what makes building and maintaining one at a useful scale practical.

## The Workflow

Every claim, edge, and source in this repository was built with the same six-stage, AI-assisted process:

1. **Source discovery.** Find candidate peer-reviewed sources for a sub-question.
2. **Source verification.** Fetch each paper or record and extract its metadata. Sources that cannot be confirmed to exist are dropped.
3. **Funding and conflict-of-interest check.** Read each source's funding or conflict-of-interest statement and classify it. A `bias_note` is added only when something specific is disclosed.
4. **Claim and edge authoring.** Write labels, claims, explanations, and tags, and choose each edge's relation. Choosing between `supports` and `depends_on` is a human decision, since crux detection depends directly on it. An AI agent can flag edges a reviewer might want to look at, but does not make the call.
5. **Structural validation.** Automated checks for schema conformance, referential integrity, and cycles.
6. **Derived-view check.** Re-run the derived views (cruxes, topic coverage, research priorities, shared authorship) and check the output makes sense. Both real errors found while building this project (a false positive in the shared-authorship check, and a funding check that copied text from the wrong page) were caught at this stage.

Human contributors follow the same process without AI, entering sources by hand in place of step 1.

[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) has the full specification, including how the stage-4 decisions are made. [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md) has the authoring conventions.

## Where this fits in the stack

- **Structure** (main focus): the `supports` / `depends_on` graph, derived hierarchy, shared ground truths, topic tags, and the Coverage tab.
- **Assessment.** The competition lists "identifying cruxes" under Assessment, so crux and double-crux detection belong here. So do:
  - the Coverage tab's one-sided topics ("surfacing missing sources or perspectives");
  - the `contested` / `contextual` tags, which separate a real open dispute from an apparent conflict that goes away once the scenario is specified ("distinguishing settled debates from performed ones");
  - dashed versus solid edges, which mark editorial judgment versus a specific citation;
  - the shared-authorship flag below.
- **Ingestion.** Every source records type, authors, year, venue, and url, plus a required `funding` classification and optional `bias_note` taken from the source's own disclosure, not guessed from venue or author (`src/models.py`, `app/detail_panel.py`). The Evidence tab in the claim popup flags when two of a claim's sources share an author (`src/ingestion.py`), since that evidence may not be independent. Not built: detecting duplicate claims across sources, or live source search. [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) covers what is and is not handled, and where the approach is weak.

## Case studies

Each case has a neutral question in `case.yaml`, separate from its root claims. A root is one side's answer; the question is what both sides are answering.

The competition provides three official case studies of different kinds (mundane but contested, confident answer with complex evidence, curated debate). All three are built here with real sources, along with a three-position philosophy case and a small synthetic case for testing.

| Case | Question | Shape | Claims / Edges / Sources |
|---|---|---|---|
| `eggs` | What are the health impacts of eggs as a human food source? | Mundane but contested. Roughly symmetric, across several independent mechanisms (cholesterol, TMAO, diabetes, saturated fat, cooking method, food safety, cancer, and others) | 21 / 23 / 47 |
| `lhc-black-holes` | Does the Large Hadron Collider pose a risk of creating synthetic black holes? | Confident answer with complex evidence. A strong scientific consensus against a few named critics, each answered individually | 17 / 16 / 24 |
| `covid-19-origins` | What are the origins of COVID-19? | Curated debate. Natural spillover is the dominant peer-reviewed view; a research-related origin is favored by some US intelligence assessments | 19 / 22 / 41 |
| `free-will` | Does free will exist? | Three positions: libertarianism, compatibilism, and hard incompatibilism | 29 / 27 / 41 |
| `toy` | Is habitual moderate coffee consumption beneficial or harmful for long-term health? | Synthetic, for testing | 7 / 7 / 2 |

The crux results differ between cases:

- `eggs`: each root rests on several independent pillars, so there is no root-level crux. The cholesterol question still shows up as a double crux in Research Priorities, at the sub-thesis level.
- `lhc-black-holes`: one crux, on the dissenting side. The safety position has several independent arguments; the risk position rests on one unresolved mechanism (extra dimensions).
- `covid-19-origins`: one crux, on the natural-spillover side. Natural spillover rules out deliberate engineering, while a research accident involving an unmodified virus does not depend on any single finding.
- `free-will`: one crux each for libertarianism (the luck argument) and hard incompatibilism (the basic-desert standard of responsibility), none for compatibilism.

The layout handles uneven cases without special-casing. `lhc-black-holes`, for example, has ten claims on one side and four on the other.

Adding a case needs no code changes, only `case.yaml`, `claims.yaml`, `edges.yaml`, and `sources.yaml` under `data/cases/<case_id>/`. See [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md).

## Running it

You only need this to run or develop the code yourself. Contributing to a case is done through the Contribute tab in the app (see [`docs/CONTRIBUTING_CLAIMS.md`](docs/CONTRIBUTING_CLAIMS.md)).

```bash
git clone <repo-url> && cd epistemology
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

The app opens at `http://localhost:8501`. The sidebar switches cases, filters by topic or text, and isolates cruxes. Clicking a node shows its explanation, sources, and edges. The Contribute tab submits a new claim, edge, or source for review.

## Validating a case

```bash
python -m src.main validate <case_id>
```

Checks schema conformance, duplicate ids, dangling references, and cycles (the layout requires an acyclic graph).

```bash
pytest tests/
```

## Project layout

```
data/cases/<case_id>/{case,claims,edges,sources}.yaml   # case data
schema/*.schema.json                                    # JSON Schema for each YAML file
src/models.py                                           # pydantic Case/Claim/Edge/Source
src/loader.py                                           # load_case, depth/reachability helpers
src/validate.py                                         # referential integrity + cycle detection
src/crux.py                                             # crux / double-crux detection
src/research_priorities.py                              # sub-thesis-aware crux ranking
src/discourse.py                                        # topic coverage/emphasis (Coverage tab)
src/ingestion.py                                        # shared-authorship flag
app/                                                    # Streamlit UI
```

## License

Code is MIT-licensed (`LICENSE`). The data under `data/` is CC-BY 4.0 (`data/LICENSE`): you can fork, extend, and merge it with credit.

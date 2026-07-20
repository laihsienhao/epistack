# Methodology

This is supporting material for judges of the Future of Life Foundation's Epistemic
Case Study Competition. It covers two things: the workflow used to build every
claim, edge, and source in this repository, and how that workflow and the
resulting claim graph relate to the competition's judging criteria, including
where the methodology is currently uncertain or incomplete. Together, the graph
and the workflow are referred to as the framework. For the mapping of specific
features onto the competition's Ingestion / Structure / Assessment taxonomy, see
[`README.md`](../README.md#where-this-fits-in-the-stack).

## The Workflow

Every claim, edge, and source in this repository was built through the same
six-stage workflow. Writing it down here makes it something a reader could
replicate or automate further, and matches the competition's own submission
category of a step-by-step human-AI workflow specification.

1. **Source discovery.** Given a sub-question to build out (for example, "does
   egg-derived TMAO raise cardiovascular risk"), identify candidate real,
   peer-reviewed sources. Output: a candidate list of papers (title, author,
   venue), nothing written yet.
2. **Source verification and metadata extraction.** For each candidate, confirm it
   is real by fetching the actual paper or its abstract or record, then extract
   structured metadata (`type`, `authors`, `year`, `venue`, `url`) matching
   `schema/source.schema.json`. Decision point: a source that cannot be verified
   as real is rejected, regardless of how plausible its title sounds.
3. **Funding and conflict-of-interest verification.** For each verified source,
   check its disclosed funding or conflict-of-interest statement: the paper's own
   text, PubMed or PMC grant metadata, Crossref funder records, or, as a last
   resort, author institutional affiliation. Classify `funding`
   (`industry | independent | government | mixed | unknown`); write `bias_note`
   only when something concrete and specific is disclosed. Decision point:
   `unknown` is the output when verification fails, not a value inferred from
   venue or author as a shortcut (see `docs/CONTRIBUTING_CLAIMS.md`).
4. **Claim and edge authoring.** Given verified sources, draft `claim.text`,
   `label`, `explanation`, and `tags` (following the label templates and
   anti-sprawl rule in `docs/CONTRIBUTING_CLAIMS.md`), then decide each edge's
   `relation`. Decision point: `supports` versus `depends_on`, the single input
   to crux detection, is currently made without automated support (the full
   decision procedure is set out below).
5. **Structural validation.** Run `python -m src.main validate <case_id>`: schema
   conformance, duplicate ids, dangling references, cycle detection. Fully
   automated.
6. **Derived-view sanity check.** Re-run the derived views (`compute_cruxes`,
   `topic_coverage`, `shared_authorship`) against the updated graph and inspect
   whether the results are sensible. A surprising derived result is a prompt to
   verify the underlying data, not a result to cite directly. This is how one of
   the errors described under Adversarial robustness below was caught: a
   shared-authorship flag did not match what the two papers' author fields said,
   once checked.

Stages 1 through 3 batch across independent sources: this project ran them as
multiple parallel AI research agents, each handling a disjoint batch, converging
back into one dataset. Stage 4, claim and edge authoring, including the
`supports`/`depends_on` decision, is currently done serially by whoever is
curating, with no automated check afterward. The full decision procedure behind
stages 2 through 4 is set out below.

A modified version of this same workflow also covers how the graph is updated
after initial construction, and splits into two modes. **Manual entry**:
a contributor follows stages 2 through 5 by hand (or with the Contribute tab's
form), starting from a source they already have rather than stage 1's
AI-driven discovery; this is how the graph can be extended with no AI
involvement at all, the same way Wikipedia's own contribution model needs
none. **AI-assisted updating**: an agent periodically runs stage 1 against
new publications on a case's existing sub-questions, proposes claims or edges
through stages 2 through 4, and a separate agent re-runs stage 6 before a
human merges the change. Only the first mode is implemented today; the second
is a natural extension of the same workflow, not a different one, and is
named again under Scalability below.

## Decision procedures: how each judgment call feeds the graph

The workflow above names four points where a human, or an AI assistant, makes a
judgment call rather than following a mechanical check. None of these need to
be built as running code to be formalized: each can be written down as an
explicit decision procedure, precise enough that a different person, or a
different model, applying it to the same source material should reach the same
label most of the time. The graph only ever sees the output of these
procedures, not the reasoning behind them, so the procedures are the actual
point of leverage over what the graph ends up saying.

### Source discovery and verification, feeding every `Source`

1. Given a sub-question, search from more than one angle: the mechanism itself,
   the epidemiological or experimental evidence for it, and any direct rebuttal
   or dissenting position. Searching only the angle that confirms the claim
   under construction is how a one-sided evidence base forms without anyone
   deciding to build one.
2. For each candidate found, look for a persistent identifier, a DOI, a PMID, or
   an equivalent, and confirm the paper exists as an independently checkable
   record (Crossref, PubMed, Semantic Scholar, or the publisher's own page), not
   just as a plausible title and author list.
3. Reject anything that cannot be matched to a real record, regardless of how
   well it would support the claim it was found for.
4. Extract `type`, `authors`, `year`, `venue`, and `url` from the verified
   record itself, not from a paraphrase or summary of it.

Every claim, crux, and coverage finding in the graph is downstream of this
step: a source that should have been rejected but was not corrupts everything
built on top of it.

### Funding and conflict-of-interest classification, feeding `Source.funding` and `Source.bias_note`

1. Check the paper's own disclosed funding or conflict-of-interest section
   first: methods, acknowledgments, or a dedicated disclosure statement.
2. If that is unavailable, check funder metadata on Crossref or grant metadata
   on PubMed or PMC.
3. If that is unavailable, check the authors' institutional affiliation for a
   disclosed funding relationship, used only to support a general
   classification, not to manufacture a specific claim the paper itself never
   made.
4. If none of the above resolves it, classify `unknown`. This is never
   inferred from venue reputation or author identity as a shortcut.
5. Write `bias_note` only when step 1 through 3 surfaced something specific and
   nameable: a named funder, a named patent or consulting relationship. An
   inference, however plausible, is not a `bias_note`.

### Contested versus contextual, feeding `Claim.tags` and the label template a claim uses

1. Gather the sources behind a claim and the sources behind any claim that
   appears to conflict with it (same topic tag, opposing conclusion).
2. Hold every relevant real-world variable fixed, the same population, dose,
   method, and timeframe, and ask whether the conflict still holds once the
   scenario is fully specified this way.
3. If the conflict persists even in a fully specified scenario, tag
   `contested`: the field has not converged.
4. If specifying the scenario resolves the apparent conflict (a difference in
   cooking method, handling, or dose explains both findings), tag `contextual`,
   and word the claim's label to name the resolving variable directly rather
   than as an open question.
5. If neither condition holds, the claim is simply supported and needs no tag.

### Edge relation, `supports` versus `depends_on`, feeding the only input to crux detection

1. State the child claim and the parent claim it points to.
2. Ask whether the parent claim would still stand, perhaps more weakly, if the
   child claim turned out to be false, or whether the parent collapses
   entirely with nothing left to hold it up.
3. If the parent still stands on other grounds, the relation is `supports`.
4. If the parent has nothing else holding it up, the relation is `depends_on`.
5. A useful check, not a substitute for the reasoning above: a parent claim
   with exactly one incoming edge should almost always have that edge as
   `depends_on`, since nothing else could be doing the work of holding it up.

### Where these four procedures meet the graph

`src/crux.py`'s `compute_cruxes_for` and `src/research_priorities.py`'s ranking
never look at a source, a funding note, or a tag directly; they only ever
traverse `Edge.relation`. Every claim the app presents as a crux, a double
crux, or a top-ranked research priority is a direct function of the edge-
relation procedure applied to the specific edges upstream of it. Likewise,
`src/discourse.py`'s Coverage tab and every `contested`/`contextual` badge in
the detail panel are a direct function of the contested-versus-contextual
procedure. None of these derived views have any way to tell a reader whether
the judgment call underneath them was applied carefully, applied loosely, or
applied by someone with a stake in the outcome; they can only be as reliable as
the procedure that produced their input.

This is the concrete shape of the auditor named under Scalability below: an
agent given a claim's text, its sources' own language, and one of these four
procedures could check whether the existing label follows the procedure or
drifts from it, and flag the difference for a reviewer. That auditor is
designed here, not built, for the `supports`/`depends_on` decision specifically,
but the same idea applies to all four procedures, since they are the same shape
of task: read the evidence, apply a fixed test, output a label.

## How this addresses the judging criteria

### Generalizability

The schema (`case.yaml` / `claims.yaml` / `edges.yaml` / `sources.yaml`) and the
workflow above have no case-specific logic anywhere in `src/` or `app/`. All
three of the competition's official case studies, `eggs`, `lhc-black-holes`, and
`covid-19-origins`, are built on this schema, and each spans a different shape:
mundane-but-contested, confident-answer-with-complex-evidence, and curated
debate respectively. Adding each case required only new YAML files under
`data/cases/<case_id>/`, with no changes to `src/` or `app/`. `toy` is a fourth,
synthetic case used to exercise the workflow's mechanics; it is not one of the
three official cases.

Modeling every case with the same two-or-more-roots primitive has a real limit
worth naming here. `lhc-black-holes` is not a symmetric rival-schools-of-thought
debate the way `eggs` is; it is an overwhelming, institutionally endorsed
consensus against a handful of named, individually rebutted critics.
Representing both cases the same structural way is consistent, since
disagreement is still structural regardless of how lopsided the two trees'
evidentiary weight is, but a reader skimming only the graph shape without
reading the claims themselves could read this as a more balanced dispute than it
is. The root-thesis text and the crux and coverage findings show the actual
asymmetry (a single-root crux for the dissenting side only, versus `eggs`'s
double-crux), but the shared "two roots" pattern can suggest more symmetry than
the underlying content has.

### Compounding and shareability

The data under `data/cases/` is the deliverable, not just the Streamlit app
around it. It is plain YAML, validated against JSON Schema
(`schema/*.schema.json`), and licensed separately under CC-BY 4.0
(`data/LICENSE`), so another team can fork, extend, or merge it independently of
the code. The Contribute tab in the app produces the same YAML shape a manual
edit would, so a new contribution is immediately mergeable rather than needing
translation into the project's format.

### Scalability

The Scalability criterion asks whether this approach gets better with more
compute, better models, or more contributors, and whether it is bottlenecked on
any single hand-designed human step. The evidence here comes from what happened
while building this submission.

Every source's `funding`/`bias_note` classification across all four cases was
backfilled by parallel AI research agents checking each paper's disclosed
funding or conflict-of-interest statement. A citation-verification pass on the
`covid-19-origins` case caught a source given to a research agent under one
author list that turned out, on verification against PubMed, Crossref, and
Semantic Scholar, to be a single-author paper by a different scientist. The
citation was corrected before it reached the graph. The same fetch-verify-
structure workflow gets cheaper and more accurate as the underlying model
improves, with no code changes required.

More compute or scrutiny improves existing checks without changing their shape.
The shared-authorship checker (`src/ingestion.py`) currently does
surname-and-initials-compatibility string matching, which sets a real ceiling: a
common enough surname-and-initials combination could still match two different
people, and in a larger corpus than this project's this would surface as false
positives. A model doing entity resolution, cross-checking institutional
affiliation and publication history, would tighten this without touching the
surrounding architecture. The same is true of funding verification: more agent
time spent cross-referencing a source's disclosure only increases confidence in
the result.

The one place this does not yet hold is edge labeling. `supports` versus
`depends_on`, the input to crux detection, is decided by human or AI-assisted
human judgment alone, with no automated check today. The decision procedure for
this call is set out above, alongside the other three judgment calls the graph
depends on; an agent applying that procedure to a claim's sources could flag
disagreements with the existing label for review, the same auditor role
described there.

The AI-assisted updating mode described under "The Workflow" above, an agent
periodically proposing new claims or edges from newly published sources, is the
same scaling argument applied to keeping a case current rather than only to
building it the first time. It is designed, not built, for the same reason the
edge-labeling auditor is not: this round of work prioritized building and
verifying three real cases over building the automation to maintain them.

#### Governance approaches for scaling contribution

How contribution scales matters as much as the schema itself, since the data
under `data/cases/` is the deliverable. This project has not yet deployed a
live, multi-contributor version of the platform: today, a single author has
been both contributor and reviewer for all four cases, the same limitation
named under Adversarial robustness above. The comparison below weighs two
ways contribution could be governed once it is deployed, against this
project's specific attack surface (mislabeled `supports`/`depends_on` edges,
ungrounded `topic:` tags, unverified `funding` classifications). Neither is a
decision this document is making in advance.

**Wikipedia-style: open, ungated editing.**
- For: scales directly with the number of contributors and with available
  compute, since a contributor can submit claims, edges, and sources through
  the Contribute tab (see `docs/CONTRIBUTING_CLAIMS.md`) at whatever rate
  review capacity allows, so no single reviewer caps throughput. Motivated
  errors are, in principle, correctable by anyone who notices them, given
  enough eyes and revision history.
- Against: "enough eyes" assumes a level of traffic none of the current cases
  have. A low-traffic case does not have Wikipedia's editor density, so a
  mistaken or bad-faith edge, tag, or funding note could sit uncorrected for a
  long time, with no checkpoint before a claim about crux status goes live.

**Peer-review-style: gated review before merge.**
- For: a designated reviewer checking `supports` versus `depends_on`
  correctness, topic-tag completeness, and funding-note accuracy before merge
  addresses this project's specific failure modes directly, most usefully for
  root theses and crux-adjacent claims, less so for a routine source-metadata
  fix.
- Against: the reviewer becomes a hand-designed human bottleneck, which the
  Scalability criterion specifically asks approaches to avoid. Throughput is
  capped by reviewer availability rather than contributor volume or model
  capability, and a single reviewer's blind spots become the project's blind
  spots.

Neither approach is implemented today. A hybrid, open submission through the
Contribute tab with review scaled to a change's blast radius so root theses
and crux-adjacent edges get more scrutiny than a new source's metadata, is a
reasonable next step but is not this document's call to make on behalf of
whoever takes the project past its current single-author stage.

### Methodological transparency

The workflow above names its decision points directly: stage 2's rule for
unverifiable sources, stage 3's `unknown`-funding rule, stage 4's
`supports`/`depends_on` judgment. "Decision procedures" above turns each of
those into an explicit, ordered test rather than leaving them as a general
principle, and `docs/CONTRIBUTING_CLAIMS.md` gives the concrete authoring
conventions (label templates, tagging rules) that stage 4 follows day to day.

Two of the competition's four named Structure sub-requirements remain open, and
are named here rather than left for a reader to notice. "Similar but not
identical" claims, different framings, caveats, or uncertainty estimates of what
is arguably the same proposition, are not structurally captured: the project's
anti-sprawl consolidation rule (`docs/CONTRIBUTING_CLAIMS.md`) currently folds
this kind of tension into one claim's `explanation` prose instead, which is in
tension with the requirement rather than meeting it. A `similar_to` edge
relation was designed in detail, direction-agnostic and requiring no
depth-merging, plus fixes to `compute_depths`/`roots()`/`_find_cycles` so a third
relation type could not silently corrupt hierarchy or trip a false cycle, but was
not built this round. Tracking structural evolution over time is also
unaddressed beyond one small step: the claim-detail popup's Evidence tab orders
sources reverse-chronologically by publication year, with the year bolded
alongside each title, so a reader can see the timeline of evidence behind a
claim. That is not the same as versioning the graph's structure itself, which
does not exist.

### Adversarial robustness

The citation-verification catch described under Scalability was caught by stage
6 of the workflow (the derived-view sanity check), not by re-reading source
code. The same stage caught an earlier version of the shared-authorship checker
flagging two different scientists named "Zhao" as the same person by matching on
surname alone; the false positive was caught by checking the two sources'
actual, differing initials, and fixed by requiring surname-and-initials
compatibility. Separately, an early funding-verification pass produced a
plausible-looking acknowledgments excerpt for one paper that turned out to be
copied from an unrelated page; this was caught by re-extracting the actual
document text rather than trusting a first-pass search result, the same stage-6
discipline.

The methodology has real, unaddressed exposure alongside those catches. Crux
detection, one of the most load-bearing outputs of this tool, rests entirely on
one distinction, `supports` versus `depends_on` (`src/crux.py`), decided by the
procedure set out above, with no automated check that a given edge follows it,
only human review at submission time. A single mislabeled edge can manufacture
a crux that should not exist, overstating how load-bearing a claim is, or hide a
real one, understating it. `src/research_priorities.py`'s ranking, which
reference points a claim is load-bearing for and how much of the graph's
structure routes through it, is built on this same edge labeling, so a
mislabeled `depends_on` edge distorts research-priority ranking as well as crux
detection, potentially pointing a reader at the wrong open question as
highest-impact.

The Coverage tab (`src/discourse.py`, `app/discourse_panel.py`) is gameable at
the tagging layer it depends on. It surfaces which side engages with which
sub-question, derived from `topic:` tags on claims, but nothing forces a
contributor to tag a claim: a motivated curator could simply never create, or
never tag, a branch on a sub-question inconvenient to their preferred side, and
the algorithm cannot distinguish "this side has nothing to say on this topic"
from "this side was never asked to engage with it." The feature makes tagged
silence visible; it does not detect untagged silence.

Funding and bias-note accuracy are bounded by both verifier diligence and source
honesty, which matters directly for resisting sources that optimize to mislead.
Every source's `funding` classification (`src/models.py`, `app/detail_panel.py`)
was checked against the source's own disclosed funding or conflict-of-interest
statement, not inferred from venue or author, but two failure modes remain
possible: a verifier, human or AI-assisted, can misread or miss a disclosure,
and a source can fail to disclose a real conflict, in which case it renders as
`independent` when it is not. This feature makes disclosed conflicts visible; it
does not detect undisclosed ones. It should be read as "here is what was
disclosed," not as a guarantee of independence.

None of this has been tested against an adversarial contributor. All four case
studies (`eggs`, `lhc-black-holes`, `covid-19-origins`, `toy`) currently have a
single author. The tagging discipline required for Coverage, the verification
discipline required for funding notes, and the labeling discipline required for
cruxes have all been exercised by one person's judgment, not stress-tested by
contributors with different priorities or incentives. The methodology's
resistance to motivated editing is argued here, not yet demonstrated in
practice.

### Insight contribution

One finding from building the Coverage tab generalizes beyond this project: a
feature derived purely from tags or labels a contributor chooses to apply is
bounded by how completely those tags were applied, in the same way the tagging
gap described under Adversarial robustness above limits the Coverage tab
specifically. The Coverage tab can show that a topic is addressed by only one
side of a debate, but it cannot distinguish that from a topic nobody thought to
tag in the first place. Any tag-driven or label-driven view of a debate is
bounded this way, regardless of how the downstream algorithm processes those
tags.

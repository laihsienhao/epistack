# Methodology: known limitations, and how this scales

This is supporting material for judges of the Future of Life Foundation's Epistemic
Case Study Competition — a direct, judge-facing account of where this tool's
methodology is genuinely uncertain or attackable, and how it scales: with compute and
model capability (its own construction pipeline is the evidence), and with more
contributors (governance models for scaling past a single author). It's written to be
read on its own, not as a continuation of `CLAUDE.md` (which is working-context memory
for picking the project back up mid-stream, not a methodology statement).

## Where this contributes across the competition's three layers

The app self-describes as targeting the **Structure** layer (README, app caption).
Checked directly against the competition's own three-layer taxonomy — Ingestion /
Structure / Assessment — that undersells the actual feature set.

**Structure** (the primary focus): inference structure (`supports`/`depends_on`,
derived hierarchy, shared ground-truths) is strong. Discourse structure (which
sub-question each side engages with, and how heavily) is now covered via `topic:`
tags, the Coverage tab, and claim/source-count weighting. Two of the competition's
four named Structure sub-requirements remain open — see "Known limitations" below.

**Assessment** (previously uncredited): the competition's site places "identifying
cruxes" under *Assessment*, not Structure — so crux/double-crux detection, this
project's flagship feature, already counts here. So does the Coverage tab's
one-sided-topic view ("surfacing missing sources or perspectives" is explicitly
named under Assessment); the `contested` vs. `contextual` tag distinction (a genuine
open dispute vs. an apparent conflict that resolves once the scenario is specified —
"distinguishing settled debates from performed ones," close to verbatim); the graph's
existing dashed-vs-solid edge rendering (a claim backed by a cited source vs. an
editorial/inferred judgment call — a structural signal toward evidential-vs-rhetorical
distinction); and the shared-authorship flag described next.

**Ingestion** (partial, real but not the focus): every source carries full provenance
metadata (`type`, `authors`, `year`, `venue`, `url`) plus a required `funding`
classification and optional `bias_note`, verified against each real source's actual
disclosed funding/COI statement rather than inferred from venue or author
(`src/models.py`, `app/detail_panel.py`). `src/ingestion.py`'s `shared_authorship()`
flags when two of a claim's own sources list an author surname in common — a
duplicate/overlap check at the metadata level that doubles as the Assessment-layer
"correlated evidence" signal above; one feature, two layers. Not built: duplicate
*claim* detection across sources, and any live resource-search capability.

## Known limitations & failure modes

Named plainly, not softened — a submission that hides its own attack surface is
worse than one that names it.

**Crux detection is only as honest as its edge labeling.** The entire crux/double-crux
feature — arguably this tool's single most valuable output — rests on one
distinction: `supports` vs. `depends_on` (`src/crux.py`). There is no automated check
that a given edge was labeled correctly; only human review at PR time. A single
mislabeled edge can manufacture a crux that shouldn't exist (overstating how
load-bearing a claim is) or hide a real one (understating it). This is the highest-
leverage way this tool's central claim could be gamed or simply gotten wrong, and
nothing in the current pipeline defends against it beyond `docs/CONTRIBUTING_CLAIMS.md`'s
guidance and reviewer attention. `src/research_priorities.py`'s ranking (which reference
points a claim is load-bearing for, and how much of the graph's structure routes
through it) is built directly on this same edge labeling, so it inherits the exact
same exposure — a mislabeled `depends_on` edge doesn't just distort crux detection,
it distorts *research-priority ranking* too, potentially pointing a reader at the
wrong open question as "highest impact." Naming this once here rather than treating
the newer feature as a separate risk.

**Two of the competition's four Structure sub-requirements remain open.** "Similar
but not identical" claims (different framings, caveats, or uncertainty estimates of
what's arguably the same proposition) aren't structurally captured — the project's
own anti-sprawl consolidation rule (`docs/CONTRIBUTING_CLAIMS.md`) currently folds
exactly this kind of tension into one claim's `explanation` prose instead, which is
in real tension with the requirement rather than satisfying it. A `similar_to` edge
relation was designed in detail (direction-agnostic, no depth-merging needed, plus
required fixes to `compute_depths`/`roots()`/`_find_cycles` so a third relation type
can't silently corrupt hierarchy or trip a false cycle) but deliberately not built
this round. Tracking structural evolution over time is also unaddressed beyond a
small honest partial step: the claim-detail popup's Evidence tab now orders sources
reverse-chronologically by publication year (newest first, with the year bolded
alongside each title rather than buried in the citation body), so a reader can see
the timeline of evidence behind a claim — real, but not the same as versioning the
graph's structure itself, which still doesn't exist.

**The discourse-coverage panel is gameable at the tagging layer.** The Coverage tab
(`src/discourse.py`, `app/discourse_panel.py`) surfaces which side actually engages
with which sub-question, derived from `topic:` tags on claims. But nothing forces a
contributor to tag a claim at all — a motivated curator can simply never create (or
never tag) a branch on a sub-question inconvenient to their preferred side, and the
algorithm has no way to distinguish "this side has nothing to say on this topic" from
"this side was never asked to engage with it." The feature makes *tagged* silence
visible; it cannot detect *untagged* silence. Naming this limitation is itself a
small insight-contribution about the whole approach, not just a disclosure about one
feature: any purely-derived, tag-driven view is bounded by how honestly the underlying
data was tagged, and no algorithm downstream of that data can fully compensate.

**Funding/bias-note accuracy is bounded by both verifier diligence and source honesty.**
Every source's `funding` classification (`src/models.py`, `app/detail_panel.py`) was
checked against the source's own disclosed funding/COI statement, not inferred from
venue or author. But two failure modes remain structurally possible: a verifier
(human or AI-assisted) can misread or miss a disclosure, and a source itself can
simply fail to disclose a real conflict — in which case it will render as
`independent` when it isn't. This feature makes disclosed conflicts visible; it does
not, and cannot, detect undisclosed ones. It should be read as "here is what was
disclosed," not "here is a guarantee of independence."

**No adversarial diversity of contributors yet.** All case studies (`eggs`,
`lhc-black-holes`, `covid-19-origins`, `toy`) currently have a single author. Every
design decision above — the tagging discipline
required for Coverage, the verification discipline required for funding notes, the
labeling discipline required for cruxes — has been exercised by one person's judgment,
not stress-tested by contributors with different priorities or incentives. The
methodology's resistance to motivated editing is, so far, argued rather than
demonstrated in practice.

**All three of the competition's official case studies now have real content.** The
competition provides `eggs`, `LHC black hole risk`, and `COVID-19 origins` —
deliberately one each of three shapes (mundane-but-contested /
confident-answer-with-complex-evidence / curated debate). `lhc-black-holes` (added
2026-07-19, ~19 real, individually funding-verified sources) demonstrated the
"confident-answer-with-complex-evidence" shape; `covid-19-origins` (added
2026-07-19, 32 real, individually funding-verified sources) demonstrates the
"curated debate" shape — the most evenly-contested of the three, with real,
disclosed industry/advocacy ties surfaced on *both* sides rather than only the side
it would be politically convenient to flag. Both required **zero application code
changes** — proving the generalizability claim on three structurally distinct real
cases rather than asserting it once, as this document previously named as the
single weakest point against the Generalizability criterion. `toy` remains
synthetic pipeline-testing, not a fourth real case.

**The LHC case's shape itself is worth naming as a limitation of the comparison.**
`lhc-black-holes` is not a symmetric rival-schools-of-thought debate the way `eggs`
is — it's an overwhelming, institutionally-endorsed consensus against a handful of
named, individually-rebutted critics. Modeling both cases with the same "two roots"
primitive is honest (disagreement is still structural, a diverging tree, regardless
of how lopsided the two trees' actual evidentiary weight is), but a reader skimming
only the graph shape without reading the claims themselves could mistake this for a
more balanced dispute than it is. The root-thesis text and the crux/coverage findings
recover the actual asymmetry (a single-root crux for the dissenting side only, versus
`eggs`'s double-crux — a real, different structural signature, not a copy), but this
is worth naming rather than letting the shared "two roots" pattern imply more
symmetry than the underlying content has.

**Shared-authorship detection is plain string matching, not verified identity.**
`src/ingestion.py`'s `shared_authorship()` flags sources listing a common surname in
the compact "Surname Initials" field. In a larger corpus with common surnames, this
would produce false positives (two different "Wang J"s flagged as one). It's sized
correctly as a hint prompting a reader to check, not an assertion — but that
scaling limit is real and worth naming before this pattern is reused on a bigger
corpus.

## Scalability: what actually demonstrates it, not just architecture

The Scalability criterion asks whether this approach gets better with more compute,
better models, or more contributors — and whether it's bottlenecked on any single
hand-designed human step. The strongest evidence here isn't hypothetical: it's what
already happened while building this submission.

**The verification work in this repo was produced by the mechanism it's arguing for.**
All 37 `eggs` sources' `funding`/`bias_note` classifications (`src/models.py`,
`data/cases/eggs/sources.yaml`) were backfilled by parallel AI research agents
checking each paper's actual disclosed funding/COI statement — not one person reading
37 papers by hand. `src/ingestion.py`'s `shared_authorship()` flag was itself debugged
this way: a false positive (two different "Zhao"s conflated by surname-only matching)
was caught by checking a primary source (a co-investigator's own CV) before being
reported, not by code inspection. The `covid-19-origins` funding-verification pass
caught a different kind of error entirely: a source citation given to a research
agent as "Quay, Muller & Young 2021" turned out, on direct fetch of the DOI against
PubMed/Crossref/Semantic Scholar, to be a single-author paper by a different
scientist (Ariel Fernández) — the citation was corrected before it reached this
graph, rather than being published on the strength of a plausible-sounding author
list. This is the "benefits as base-model capability rises" bullet in action, not an
argument for it: the same fetch-verify-structure pipeline (formalized below) gets
cheaper and more accurate as the underlying model improves, with zero code changes
required.

**More compute/scrutiny strictly improves existing checks, never degrades them.** The
shared-authorship checker currently does surname+initials-compatibility string
matching (`_initials_compatible` in `src/ingestion.py`), which is why "Known
limitations" above names a real ceiling: a sufficiently common surname+initials
combination could still coincidentally match two different people. A more capable
model doing genuine entity resolution (cross-checking institutional affiliation,
publication history) would strictly tighten this without touching the surrounding
architecture — the check's *output* improves, its *shape* doesn't need to change. The
same is true of funding verification: spending more agent-time cross-referencing a
source's disclosure only ever increases confidence, never decreases it.

**The one place this property doesn't yet hold: edge labeling.** `supports` vs.
`depends_on` — the single input to crux detection, this project's flagship feature —
is decided by human (or AI-assisted human) judgment alone, with no automated check
today. This is the one genuine exception to an otherwise-scalable pipeline: nothing
currently spends compute verifying that this specific judgment call was made
correctly, even though the same fetch-verify pattern used for funding/authorship would
apply directly — an agent given a claim's text and its source(s) could check whether
the source's own language supports a "necessary condition" reading vs. a "contributing
evidence" one, and flag disagreements for review. Designed here, explicitly not yet
built, given the deadline — the highest-leverage next step for this specific
criterion.

### The claim-construction pipeline, formalized

Everything above refers to one underlying workflow, used to build every claim/edge/
source in this repo. Written down explicitly here because a scalability argument that
only exists as prose is weaker than one a reader could actually replicate or automate
further — this is also, in the competition's own submission-type language, a
"specification describing a step-by-step human-AI workflow."

1. **Source discovery.** Given a sub-question to build out (e.g. "does egg-derived
   TMAO raise cardiovascular risk"), identify candidate real, peer-reviewed sources.
   Output: a candidate list of papers (title/author/venue), nothing written yet.
2. **Source verification & metadata extraction.** For each candidate, confirm it's
   real — not fabricated — by fetching the actual paper or its abstract/record, then
   extract structured metadata (`type`, `authors`, `year`, `venue`, `url`) matching
   `schema/source.schema.json`. *Decision point*: a source that can't be verified as
   real is rejected outright, never included on the strength of a plausible-sounding
   title alone.
3. **Funding/COI verification.** For each verified source, check its actual disclosed
   funding/COI statement — the paper's own text, PubMed/PMC grant metadata, Crossref
   funder records, or (last resort) author institutional affiliation. Classify
   `funding` (`industry | independent | government | mixed | unknown`); write
   `bias_note` only when something concrete and specific is disclosed. *Decision
   point*: `unknown` is the honest output when verification genuinely fails —
   never inferred from venue/author as a shortcut (see `docs/CONTRIBUTING_CLAIMS.md`).
4. **Claim & edge authoring.** Given verified sources, draft `claim.text` / `label` /
   `explanation` / `tags` (following the label templates and anti-sprawl rule in
   `docs/CONTRIBUTING_CLAIMS.md`), then decide each edge's `relation`. *Decision
   point*: `supports` vs. `depends_on` — the single highest-leverage judgment call in
   the whole pipeline (see "Known limitations" above), currently made without
   automated support.
5. **Structural validation.** Run `python -m src.main validate <case_id>` — schema
   conformance, duplicate ids, dangling references, cycle detection. Mechanical,
   already fully automated.
6. **Derived-view sanity check.** Re-run the derived views (`compute_cruxes`,
   `topic_coverage`, `shared_authorship`) against the updated graph and inspect
   whether the results are sensible. This is how the Zhao false positive described
   above was actually caught — not by re-reading `src/ingestion.py`'s code, but by
   noticing a *derived output* (a shared-authorship flag) didn't match the
   *underlying data* (the two papers' actual, different author initials) once
   checked. Treat a surprising derived result as a prompt to verify, not as ground
   truth to cite directly.

**Parallelization, and where it currently stops.** Stages 1–3 batch cleanly across
independent sources — this session ran them as 5+ parallel AI research agents, each
handling a disjoint batch, converging back into one dataset (the 37-source funding
backfill), with two agents independently resuming from a stalled state without losing
progress. Stage 4 is where parallelization currently stops: claim/edge authoring, and
specifically the `supports`/`depends_on` decision, is done serially by whoever's
curating, with no automated check afterward. Extending stages 1–3's pattern to an
adversarial audit of stage 4's decisions specifically is the concrete next step named
above, not a vague aspiration.

## Scaling contribution: two governance models

This project's actual deliverable is the data under `data/cases/`, not just the app
(`docs/CONTRIBUTING_CLAIMS.md`) — so how contribution scales matters as much as the
schema itself. Today, the project runs neither model below in a formalized way: it's
an informal, ungated process — anyone can open a PR against `data/cases/`, and there
is no documented review gate at all. The comparison below is a neutral account of two
ways this could be scaled up, weighed against this project's specific attack surface
(mislabeled `supports`/`depends_on` edges, ungrounded `topic:` tags, unverified
`funding` classifications) — not a recommendation for one over the other.

**Wikipedia-style: open, ungated editing.**
- *For*: scales directly with the number of contributors and with available compute
  (an AI-assisted contributor can propose claims/edges/sources at whatever rate
  review capacity allows) — no single reviewer is a bottleneck on throughput. This is
  the shape of contribution the Scalability criterion rewards most directly.
  Motivated errors are, in principle, correctable by anyone who notices them, given
  enough eyes and enough revision history.
- *Against*: "enough eyes" is doing real work in that sentence — a low-traffic case
  (which every case here currently is) doesn't have Wikipedia's actual editor density,
  so a bad-faith or simply mistaken edge/tag/funding-note could sit uncorrected for a
  long time. There's no built-in checkpoint before a claim about, say, crux status
  goes live.

**Peer-review-style: gated review before merge.**
- *For*: a designated reviewer checking `supports` vs. `depends_on` correctness, topic-
  tag completeness, and funding-note accuracy before merge directly defends against
  this project's specific highest-leverage failure modes — the reviewer is exactly the
  checkpoint the open model lacks. Most valuable where mislabeling does the most
  damage: root theses and crux-adjacent claims specifically, less critical for e.g. a
  routine source metadata fix.
  - *Against*: the reviewer becomes a literal hand-designed human bottleneck — directly
  in tension with the Scalability criterion's "not bottlenecked on any single
  hand-designed human step." Throughput is capped by reviewer availability rather than
  by contributor volume or model capability, and a single reviewer's own blind spots
  become the project's blind spots.

Neither model is implemented today. A future pass could reasonably land on a hybrid —
lighter-weight review scaled to a change's blast radius (root theses and crux-adjacent
edges reviewed more carefully than a new source's metadata) — but that's a judgment
call for whoever takes this project past its current single-author stage, not one
this document is making on their behalf.

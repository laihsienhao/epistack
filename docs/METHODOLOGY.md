# Methodology: known limitations, and how this scales with contributors

This is supporting material for judges of the Future of Life Foundation's Epistemic
Case Study Competition — a direct, judge-facing account of where this tool's
methodology is genuinely uncertain or attackable, and how contribution to it could
scale beyond a single author. It's written to be read on its own, not as a
continuation of `CLAUDE.md` (which is working-context memory for picking the project
back up mid-stream, not a methodology statement).

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
guidance and reviewer attention.

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
graph's structure itself,
which still doesn't exist.

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

**No adversarial diversity of contributors yet.** Both case studies (`eggs`, `toy`)
currently have a single author. Every design decision above — the tagging discipline
required for Coverage, the verification discipline required for funding notes, the
labeling discipline required for cruxes — has been exercised by one person's judgment,
not stress-tested by contributors with different priorities or incentives. The
methodology's resistance to motivated editing is, so far, argued rather than
demonstrated in practice.

**Only one of the competition's three official case studies has real content.** The
competition provides `eggs`, `COVID-19 origins`, and `LHC black hole risk` —
deliberately one each of three shapes (mundane-but-contested / curated debate /
confident-answer-with-complex-evidence). This project only builds out the eggs shape;
`toy` is synthetic pipeline-testing, not a second real case. The "zero-code-change
generalizability" claim (`docs/CONTRIBUTING_CLAIMS.md`) is true by construction —
nothing in `app/` references `eggs` by name — but it is *architectural*, not yet
*demonstrated* on the other two officially-provided shapes. This is the single
weakest point against the Generalizability criterion's explicit "not narrowly overfit
to the provided case studies" bar, and it's named here rather than left for a judge
to discover.

**Shared-authorship detection is plain string matching, not verified identity.**
`src/ingestion.py`'s `shared_authorship()` flags sources listing a common surname in
the compact "Surname Initials" field. In a larger corpus with common surnames, this
would produce false positives (two different "Wang J"s flagged as one). It's sized
correctly as a hint prompting a reader to check, not an assertion — but that
scaling limit is real and worth naming before this pattern is reused on a bigger
corpus.

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

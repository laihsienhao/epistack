# Contributing to a claim graph

This project treats each case as a shared, living graph, closer to a Wikipedia
article than a codebase: the goal is a compounding artifact that anyone can
extend, not a private dataset. Contributing does not require cloning a
repository, installing anything, or writing YAML by hand. It happens directly
on the platform. This document covers how to add to an existing case, or
propose a new one, and is the content-quality reference for stage 4 (claim and
edge authoring) of the workflow described in
[`docs/METHODOLOGY.md`](METHODOLOGY.md), whether that stage is carried out by
a contributor directly or with AI assistance.

## Adding a claim, edge, or source to an existing case

Open the case on the platform, go to the **Contribute** tab, and fill in the
form for whatever you are adding, a claim, an edge, or a source. Submit it
from there; there is no file to download, edit, or upload.

Your submission is queued for review before it becomes part of the shared
graph, the same review a claim, edge, or source has always gone through in
this project (see `docs/METHODOLOGY.md`'s workflow, stage 4, and the
governance discussion under Scalability). A reviewer checks it against the
guidance in this document, principally whether `supports` versus `depends_on`
was judged correctly, since that is what the rest of the graph's structure is
computed from, and whether a `contested`/`contextual` tag and funding
classification are backed by something real rather than asserted. Once
reviewed, your contribution is merged into the case and immediately visible
to every reader.

Structural checks (schema conformance, referential integrity, no cycles) run
automatically before anything goes live, the same
`python -m src.main validate <case_id>` check described in
`docs/METHODOLOGY.md`, so a submission cannot silently corrupt the graph's
hierarchy even before a human reviewer looks at its content.

## Schema at a glance

The fields below are what the Contribute form's inputs map to; contributing
through the platform never requires writing or editing them directly, but
knowing what each one means is what separates a well-formed submission from
one a reviewer has to send back.

**Case** (`schema/case.schema.json`, `case.yaml`): just `question`, the neutral
problem the case explores, not a position on it. See "Proposing a new case
study" below for authoring guidance.

**Claim** (`schema/claim.schema.json`): `id`, `case`, `text` (the precise claim
statement, shown in the detail panel and cruxes list, which can be as long as it
needs to be to stay accurate), `label` (required: a summary of `text` in well
under 15 words, written for a small circle on a graph; never `text` truncated with
an ellipsis, see below), `explanation` (optional, longer markdown shown when the
node is expanded; if it narrates more than one finding, break it into separate
paragraphs with a blank line between them rather than one dense block, since one
paragraph per finding reads far more scannably in the detail-panel popup than a
wall of text conveying the same content. See any claim in
`data/cases/eggs/claims.yaml` with more than one citation for the pattern, written
as a YAML folded block scalar (`explanation: >-`) so the source file stays
readable too), `status` (`draft` or `reviewed`: a curation flag, not a
contestedness flag; contestedness is structural, see below), `tags`, `sources`
(ids into `sources.yaml`), `confidence` (leave `null`, reserved for the
Assessment-layer stretch goal), `author`, `created`.

### Writing a good label

A label should read as a complete thought on its own, in plain language, not an
academic sentence fragment, and it must follow one of the two fixed templates
below depending on the claim's role. Never truncate `text` with an ellipsis, and
never tag it with its evidence type: no "Study:", "Trial:", "Meta-analysis:",
"Guideline:", or "Fact:" prefixes. A node represents a broad claim or argument,
not a report of one finding, so its label should always read that way, even for a
single-fact node.

Bad: "In a pooled analysis of 6 large US prospective cohorts (n=29,615; median
follow-up 17.5 ye..." (truncated), or "Study: more cholesterol, higher death risk"
(tagged with evidence type).

Good: "More cholesterol is linked to higher death risk."

The label is what a reader sees first. It has to earn a second look at the full
`text`, not just serve as a shorter version of it.

- **Claim, thesis, or shared fact** (anything that is not itself an open
  question): a plain sentence-case clause, no tag, no trailing punctuation. This
  covers root theses ("Egg cholesterol meaningfully raises heart disease and death
  risk"), sub-theses, synthesis or argument nodes built from several sources, and
  standalone shared-fact nodes alike ("One egg has about 200mg of cholesterol,
  mostly in the yolk"). There is no separate tagged template for facts or
  findings. The specific studies, trials, and analyses behind a claim belong in
  its `sources` list and `explanation` prose, not in the label; see "Avoid
  one-node-per-finding sprawl" below for why almost nothing should be a
  single-source finding node in the first place.
- **Open-question or contested claim** (the claim itself is the unresolved crux,
  not a finding, tagged `contested`, see "Contested versus contextual claims"
  below): `Whether <clause> is unresolved` or `Whether <clause> is contested`, no
  trailing punctuation. For example: "Whether egg cholesterol truly causes heart
  disease is unresolved."

### Contested versus contextual claims

Not every claim that is not a clean yes-or-no answer is unsettled in the same way,
and the two are tagged and worded differently.

- **`contested`**: a genuine open dispute, where real evidence pulls in both
  directions even once you specify a realistic scenario, and the field has not
  converged. Use the open-question label template above (`Whether X is
  contested/unresolved`), since the claim really is a live question, not yet a
  settled fact. Example: `tmao-cvd-risk-contested`. Dose-response trials show eggs
  raise TMAO, a rebuttal trial found whole-egg choline specifically does not raise
  fasting TMAO, and a later meta-analysis found no pooled effect; the tension
  persists even for whole-egg consumption specifically.
- **`contextual`**: the apparent conflict is explained by a concrete, nameable
  real-world variable (how something is prepared, handled, or sourced), and once
  you specify which case you are in, the answer is fairly clear on each side. This
  is a claim, not an open question, so it uses the plain-clause template rather
  than the `Whether X` template, phrased to foreground the resolving variable.
  Example: `cooking-oxidation-cop-contested`, worded as "Egg cooking method and
  storage determine cholesterol-oxidation risk" (frying or long storage clearly
  raises oxidation products; quick home cooking clearly does not), not as
  "whether cooking oxidation is a real risk is contested," which would wrongly
  suggest the science itself is unresolved.

Both tags are informational and organizational: they drive the label wording
convention above, but there is no distinct node color or border for them. A
reader currently spots a nuanced claim by reading its label or text, not by a
visual channel on the node itself.

### Topic tags (discourse structure)

Alongside the status and side tags above, add one or more `topic:<name>` entries
to a claim's `tags` list to mark which sub-question it addresses (for example,
`topic:cholesterol`, `topic:tmao`), in kebab-case with no spaces. This powers the
**Coverage** tab (`src/discourse.py`, `app/discourse_panel.py`): a topic reachable
from two or more roots is a shared, contested sub-question both sides engage
with, even if they draw opposite conclusions from it; a topic reachable from
exactly one root is a sub-question only that side has built out. A claim can
carry more than one topic tag when it truly spans two sub-questions. For example,
`tmao-cvd-risk-contested` carries both `topic:choline` and `topic:tmao`, since
TMAO risk is the choline-metabolism pathway, and tagging it `topic:choline` is
what makes it register as shared with the `egg-choline-benefit` branch on the
other side. Do not invent a topic tag just to force a claim into the shared
bucket; see `docs/METHODOLOGY.md` for why this tagging step is itself a named
limitation of the Coverage view, not a fully mechanical derivation.

### Source funding and bias transparency

Every source requires a `funding` field (`industry | independent | government |
mixed | unknown`), rendered as a badge on every citation card in the detail panel
alongside the `type` field. Determine this by checking the paper's own funding,
acknowledgments, or conflict-of-interest disclosure, via the paper's page, its
PubMed record, or its full text, never by inferring from venue or author name
alone. Use `unknown` only when it is truly undeterminable after checking, not as
a shortcut. Add an optional `bias_note` (plain string) only when something
concrete and specific is disclosed (for example, "Funded by the Egg Nutrition
Center," or a named industry-linked patent or consulting relationship); do not
editorialize or speculate beyond what is disclosed. This is structural
transparency, not a quality score: it sits deliberately outside the `confidence`
field (still reserved, still `null`, for the Assessment-layer stretch goal). A
source's funding origin is a fact about where it came from, not a judgment about
whether its findings are correct.

### Avoid one-node-per-finding sprawl

Only give a finding its own standalone node when it is an independently reachable
**shared ground truth** used by two or more branches (for example, a basic content
fact like "one egg has about 200mg of cholesterol"), or when it is itself the
claim under dispute (a crux or contested node). If a finding's only role is to
support exactly one parent claim, do not create a node for it; fold its citation
into that parent's `sources` list and narrate the finding in the parent's
`explanation` prose instead. The detail panel already renders every source in
`claim.sources` as a full citation card (title, authors, year, venue, link), so
merging several studies onto one claim loses no citation fidelity. It keeps the
graph itself readable as a set of broad claims and arguments rather than a forest
of single-study leaves. A claim built this way is a synthesis of several sources,
not a report of one finding, so it uses the same plain-clause label template as
any other claim or thesis, never a tagged one, even for the rare standalone
shared-fact node described above.

## Edge and source schema

**Edge** (`schema/edge.schema.json`): `id`, `relation` (`supports` or
`depends_on` only, see below), `from` and `to`. Direction always runs from the
more specific or derived claim to the more general one it relates to, regardless
of relation type. `provenance` is the source id or ids that assert this specific
relation, and may be empty, with `author` set, for an editorial or inferred
judgment rather than something a paper explicitly states.

**Source** (`schema/source.schema.json`): a bibliography entry with `id`, `type`
(`rct | meta_analysis | cohort | review | guideline | news | other`), `title`,
`authors`, `year`, `venue`, `url`, `funding` (required, see above), and
`bias_note` (optional). Use real, verifiable citations; a fabricated or
unverified citation defeats the entire point of this tool.

Write `authors` as a plain comma-separated "Surname Initials" shorthand (for
example, `"Zhong VW, Van Horn L, Cornelis MC"`), not a pre-formatted citation.
The detail panel (`app/detail_panel.py`) derives a full APA-style reference from
`authors`, `year`, `title`, and `venue` at render time, the same way the graph's
structure is never stored pre-computed. An organizational author (for example,
`"U.S. Food and Drug Administration"`) or an already-truncated `"Surname M, et
al."` are both handled as written. Write `venue` as `"Journal Name,
volume(issue):pages"` (a colon before the page range); the formatter converts
that to APA's `volume(issue), pages` comma form automatically.

## Choosing `supports` versus `depends_on`

This choice is not cosmetic; it drives crux detection.

- **`supports`**: this claim is evidence for the claim it points to, but that
  claim would still stand, perhaps more weakly, without it. Use this for the
  common case, since most evidence is one contributing consideration among
  several.
- **`depends_on`**: the claim it points to cannot hold without this one. Use this
  sparingly, only when you would say "if this turned out false, the argument
  above it does not just weaken, it collapses." Claims connected via a
  `depends_on` chain up to a root are automatically surfaced as **cruxes**; a
  claim that is a crux for two or more roots is a **double crux**, the
  highest-value node in the graph. Be deliberate here: mislabeling `supports` as
  `depends_on`, or the reverse, directly distorts what the tool tells a reader is
  load-bearing.

## No `contradicts` relation: model disagreement structurally instead

Rival positions are separate root claims (nodes with no outgoing edges), not two
claims joined by a `contradicts` edge. If you are adding a claim that argues
against an existing root, either:

- point it (via `supports` or `depends_on`) toward a different root representing
  the rival position, creating that root first if it does not exist yet, or
- if it is a foundational fact both sides would accept, let it feed into both
  trees; it will automatically render as a shared ground truth, and, if it is an
  open question rather than a settled fact, potentially a double crux.

## Proposing a new case study

Propose a new case from the platform the same way you would add to an existing
one, no separate setup step.

1. State the case's neutral framing question, the shared problem both sides
   are answering (for example, "What are the health impacts of eggs as a human
   food source?"), not a position on it. This is authored, not derived: unlike
   hierarchy, cruxes, or topic coverage, there is no mechanical way to produce
   the shared question from the root claims themselves, since a root is one
   side's answer, not the question both sides are answering.
2. Identify the competing root claims (schools of thought) for the topic.
3. Submit real sources first, then build claims and edges from them, through
   the same Contribute flow as adding to an existing case.
4. The same automated structural check and review step described above apply
   before the new case appears alongside the others.

No application code changes are needed for a new case to appear once it is
approved: the case selector picks up any case in the shared graph
automatically, the same way it already does for `eggs`, `lhc-black-holes`,
`covid-19-origins`, and `toy`. Under the hood, a case is stored as
`case.yaml` / `claims.yaml` / `edges.yaml` / `sources.yaml`, plain YAML
matching the schema in `schema/*.schema.json`, though contributing to it never
requires touching those files directly.

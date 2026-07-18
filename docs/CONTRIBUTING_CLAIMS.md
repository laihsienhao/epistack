# Contributing to a claim graph

This project's actual deliverable is the data under `data/cases/`, not just the app —
the goal is a "compounding" artifact other people can extend. This doc covers how to
add to an existing case, or start a new one.

## Adding a claim or edge to an existing case

Easiest path: run the app (`streamlit run app/app.py`), open the **Contribute** tab
for the case, fill in the form, and download the generated YAML snippet. Then:

1. Open `data/cases/<case_id>/claims.yaml` (or `edges.yaml`) and paste the new entry
   in, keeping the existing entries untouched.
2. Run `python -m src.main validate <case_id>` and fix anything it flags.
3. Open a PR.

You can also edit the YAML files directly — they're plain, human-readable YAML, no
tooling required.

## Schema at a glance

**Case** (`schema/case.schema.json`, `case.yaml`): just `question` — the neutral
problem the case explores, not a position on it. See "Starting a new case study"
below for the authoring guidance.

**Claim** (`schema/claim.schema.json`): `id`, `case`, `text` (the precise claim
statement — shown in the detail panel and cruxes list, can be as long as it needs to
be to be accurate), `label` (**required** — a genuine summary of `text` in well under
15 words, written for a small circle on a graph; never just `text` truncated with an
ellipsis — see below), `explanation` (optional, longer markdown shown when the node is
expanded — if it narrates more than one finding, break it into separate paragraphs
(blank line between them) rather than one dense multi-sentence block; one paragraph
per finding/study reads far more scannably in the detail-panel popup than a wall of
text, even though it's the same content either way — see any claim in
`data/cases/eggs/claims.yaml` with more than one citation for the pattern, written as
a YAML folded block scalar (`explanation: >-`) so the source file stays readable too),
`status` (`draft` or `reviewed` — this is a curation flag, not a
contestedness flag; contestedness is structural, see below), `tags`, `sources` (ids
into `sources.yaml`), `confidence` (leave `null` — reserved for the Assessment-layer
stretch goal), `author`, `created`.

**Writing a good `label`:** it should read as a complete thought on its own, in plain
language, not an academic sentence fragment, and it must follow one of two fixed
templates below depending on the claim's role. Never just `text` truncated with an
ellipsis, and **never tag it with its evidence type** — no "Study:", "Trial:",
"Meta-analysis:", "Guideline:", or "Fact:" prefixes, ever. A node represents a broad
claim or argument, not a report of one finding, so its label should always read that
way, even for a single-fact node. Bad: "In a pooled analysis of 6 large US prospective
cohorts (n=29,615; median follow-up 17.5 ye…" (truncated) or "Study: more cholesterol,
higher death risk" (tagged with evidence type). Good: "More cholesterol is linked to
higher death risk". The label is what a reader sees first — it has to earn a second
look at the full `text`, not just be a shorter version of it.

- **Claim, thesis, or shared fact** (anything that isn't itself an open question): a
  plain sentence-case clause, no tag, no trailing punctuation. This covers root theses
  ("Egg cholesterol meaningfully raises heart disease and death risk"), sub-theses,
  synthesis/argument nodes built from several sources, and standalone shared-fact
  nodes alike ("One egg has about 200mg of cholesterol, mostly in the yolk") — there is
  no separate tagged template for facts or findings. The specific studies, trials, and
  analyses behind a claim belong in its `sources` list and `explanation` prose (shown
  in the detail-panel popup on click), not in the label — see "Avoid one-node-per-
  finding sprawl" below for why almost nothing should be a single-source finding node
  in the first place.
- **Open-question / contested claim** (the claim itself is the unresolved crux, not a
  finding, tagged `contested` — see "Contested vs. contextual claims" below): `Whether
  <clause> is unresolved` or `Whether <clause> is contested`, no trailing punctuation.
  E.g. "Whether egg cholesterol truly causes heart disease is unresolved".

**Contested vs. contextual claims.** Not every claim that "isn't a clean yes/no" is
the same kind of unsettled, and the two are tagged and worded differently:

- **`contested`** — a genuine open dispute: real evidence pulls in both directions
  even once you specify a realistic scenario, and the field hasn't converged. Use the
  open-question label template above (`Whether X is contested/unresolved`), since the
  claim really is a live question, not yet a settled fact. E.g.
  `tmao-cvd-risk-contested` — dose-response trials show eggs raise TMAO, a rebuttal
  trial found whole-egg choline specifically doesn't raise fasting TMAO, and a 2025
  meta-analysis found no pooled effect; the tension persists even for whole-egg
  consumption specifically.
- **`contextual`** — the apparent conflict is actually explained by a concrete,
  nameable real-world variable (how something is prepared, handled, or sourced), and
  once you specify which case you're in, the answer is fairly clear on each side. This
  is a **claim, not an open question**, so it uses the plain-clause template, not the
  `Whether X` template — phrase it to foreground the resolving variable. E.g.
  `cooking-oxidation-cop-contested`: "Egg cooking method and storage determine
  cholesterol-oxidation risk" (frying/long storage clearly raises COPs; quick
  home-cooking clearly doesn't) — not "whether cooking oxidation is a real risk is
  contested," which would wrongly suggest the science itself is unresolved.

Both tags are currently informational/organizational only — they drive the label
wording convention above, but no distinct node color or border. A fill-color
treatment and a dashed-border treatment were each tried and then explicitly reverted
(see CLAUDE.md's Design system entry for that history) — a reader currently spots a
nuanced claim by reading its label/text, not by a visual channel on the node itself.

**Topic tags (discourse structure).** Alongside the status/side tags above, add one
or more `topic:<name>` entries to a claim's `tags` list to mark which sub-question it
addresses (e.g. `topic:cholesterol`, `topic:tmao`) — kebab-case, no spaces. This is
what powers the **Coverage** tab (`src/discourse.py`, `app/discourse_panel.py`): a
topic reachable from two or more roots is a genuinely shared/contested sub-question
both sides engage with (even if they draw opposite conclusions from it); a topic
reachable from exactly one root is a sub-question only that side has built out. A
claim can carry more than one topic tag when it genuinely spans two sub-questions
(e.g. `tmao-cvd-risk-contested` carries both `topic:choline` and `topic:tmao`, since
TMAO risk *is* the choline-metabolism pathway, and tagging it `topic:choline` is what
makes it register as shared with the `egg-choline-benefit` branch on the other side).
Don't invent a topic tag just to force a claim into the "shared" bucket — see
`docs/METHODOLOGY.md` for why this tagging step is itself a named limitation of the
Coverage view, not a fully mechanical derivation.

**Source funding & bias transparency.** Every source now requires a `funding` field
(`industry | independent | government | mixed | unknown`), rendered as a badge on
every citation card in the detail panel alongside the (pre-existing but previously
unrendered) `type` field. Determine this by actually checking the paper's own
funding/acknowledgments/conflict-of-interest disclosure — via the paper's page,
PubMed record, or full text — never by inferring from venue or author name alone.
Use `unknown` only when genuinely undeterminable after checking, not as a shortcut.
Add an optional `bias_note` (plain string) only when something concrete and specific
is actually disclosed (e.g. "Funded by the Egg Nutrition Center," or a named
industry-linked patent/consulting relationship) — don't editorialize or speculate
beyond what's disclosed. This is structural transparency, not a quality score: it
sits deliberately outside the `confidence` field (still reserved, still `null`, for
the Assessment-layer stretch goal) — a source's funding origin is a fact about where
it came from, not a judgment about whether its findings are correct.

**Avoid one-node-per-finding sprawl.** Only give a finding its own standalone node
when it is a genuine, independently reachable **shared ground truth** used by 2+
branches (e.g. a basic content fact like "one egg has ~200mg of cholesterol") or is
itself the claim under dispute (a crux/contested node). If a finding's only role is to
support exactly one parent claim, don't create a node for it — fold its citation into
that parent's `sources` list and narrate the finding in the parent's `explanation`
prose instead. The detail panel already renders every source in `claim.sources` as a
full citation card (title/authors/year/venue/link), so merging several studies onto
one claim loses no citation fidelity — it just keeps the graph itself readable as a
set of broad claims/arguments rather than a forest of single-study leaves. A claim
built this way is a **synthesis of several sources**, not a report of one finding, so
it uses the same plain-clause label template as any other claim/thesis — never a
tagged one, even the rare standalone shared-fact node described above.

**Edge** (`schema/edge.schema.json`): `id`, `relation` (`supports` or `depends_on`
only — see below), `from` and `to` — **direction always runs from the more
specific/derived claim to the more general one it relates to**, regardless of
relation type. `provenance` is the source id(s) that assert this specific relation
(may be empty, with `author` set, for an editorial/inferred judgment rather than
something a paper explicitly states).

**Source** (`schema/source.schema.json`): a bibliography entry — `id`, `type`
(`rct | meta_analysis | cohort | review | guideline | news | other`), `title`,
`authors`, `year`, `venue`, `url`, `funding` (required —
`industry | independent | government | mixed | unknown`, see below), `bias_note`
(optional). Use real, verifiable citations — a fabricated or unverified citation
defeats the entire point of this tool.

Write `authors` as a plain comma-separated "Surname Initials" shorthand (e.g.
`"Zhong VW, Van Horn L, Cornelis MC"`), not a pre-formatted citation — the detail
panel (`app/detail_panel.py`) derives a full APA-style reference from `authors`,
`year`, `title`, and `venue` at render time, same as the graph's structure is never
stored pre-computed. An organizational author (`"U.S. Food and Drug
Administration"`) or an already-truncated `"Surname M, et al."` are both handled
as-is. Write `venue` as `"Journal Name, volume(issue):pages"` (colon before the
page range) — the formatter converts that to APA's `volume(issue), pages` comma
form automatically.

## Choosing `supports` vs `depends_on`

This choice is not cosmetic — it drives crux detection.

- **`supports`**: this claim is evidence for the claim it points to, but that claim
  would still stand (perhaps more weakly) without it. Use this for the common case —
  most evidence is one contributing consideration among several.
- **`depends_on`**: the claim it points to *cannot* hold without this one. Use this
  sparingly, only when you'd say "if this turned out false, the argument above it
  doesn't just weaken — it collapses." Claims connected via a `depends_on` chain up
  to a root are automatically surfaced as **cruxes**; a claim that's a crux for two
  or more roots is a **double crux** — the highest-value node in the graph. Be
  deliberate here: mislabeling `supports` as `depends_on` (or vice versa) directly
  distorts what the tool tells a reader is load-bearing.

## No `contradicts` relation — model disagreement structurally instead

Rival positions are **separate root claims** (nodes with no outgoing edges), not two
claims joined by a `contradicts` edge. If you're adding a claim that argues against
an existing root, either:

- point it (via `supports` or `depends_on`) toward a *different* root representing
  the rival position — creating that root first if it doesn't exist yet — or
- if it's a foundational fact both sides would accept, let it feed into both trees;
  it will automatically render as a shared ground-truth (and, if it's a genuinely
  open question rather than a settled fact, potentially a double crux).

## Starting a new case study

1. Create `data/cases/<case_id>/` with `case.yaml`, `claims.yaml`, `edges.yaml`,
   `sources.yaml`.
2. Write `case.yaml`'s `question` — the neutral problem the case explores (e.g.
   "What are the health impacts of eggs as a human food source?"), not a position on
   it. This is authored, not derived: unlike hierarchy, cruxes, or topic coverage,
   there's no mechanical way to produce the shared question from the root claims
   themselves, since a root is one side's *answer*, not the question both sides are
   answering.
3. Identify the competing root claims (schools of thought) for the topic.
4. Gather real sources first (`sources.yaml`), then build claims and edges from them.
5. Run `python -m src.main validate <case_id>` until clean.

No application code changes needed — the case selector in `app/app.py` picks up any
directory under `data/cases/` automatically.

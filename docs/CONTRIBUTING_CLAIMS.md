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

**Claim** (`schema/claim.schema.json`): `id`, `case`, `text` (the precise claim
statement — shown in the detail panel and cruxes list, can be as long as it needs to
be to be accurate), `label` (**required** — a genuine summary of `text` in well under
15 words, written for a small circle on a graph; never just `text` truncated with an
ellipsis — see below), `explanation` (optional, longer markdown shown when the node is
expanded), `status` (`draft` or `reviewed` — this is a curation flag, not a
contestedness flag; contestedness is structural, see below), `tags`, `sources` (ids
into `sources.yaml`), `confidence` (leave `null` — reserved for the Assessment-layer
stretch goal), `author`, `created`.

**Writing a good `label`:** it should read as a complete thought on its own, in plain
language, not an academic sentence fragment, and it must follow one of three fixed
templates below depending on the claim's role. Never just `text` truncated with an
ellipsis. Bad: "In a pooled analysis of 6 large US prospective cohorts (n=29,615;
median follow-up 17.5 ye…" (truncated). Good: "Study: more cholesterol, higher death
risk". The label is what a reader sees first — it has to earn a second look at the
full `text`, not just be a shorter version of it.

- **Root thesis** (no outgoing edges — a school of thought): a plain sentence-case
  clause, no tag, no trailing punctuation. E.g. "Egg cholesterol meaningfully raises
  heart disease and death risk".
- **Evidentiary claim** (reports a finding from a source, or a basic fact — see "Avoid
  one-node-per-finding sprawl" just below before creating one of these): `<tag>:
  <lowercase clause>`, no trailing punctuation. The tag is one of a **fixed, generic
  vocabulary** — never an organization name or a specific qualifying detail (no "AHA",
  no "31-year Finnish cohort", no "Same study"):
  - `Trial` — a randomized controlled trial
  - `Study` — an observational/cohort study, or a guideline body's own supporting study
  - `Meta-analysis` — a pooled analysis across multiple studies
  - `Guideline` — an official recommendation
  - `Fact` — a basic, uncontested fact

  E.g. "Study: more cholesterol, higher death risk", "Trial: egg cholesterol didn't
  raise LDL — saturated fat did", "Fact: one egg has about 200mg of cholesterol,
  mostly in the yolk".
- **Open-question / contested claim** (the claim itself is the unresolved crux, not a
  finding): `Whether <clause> is unresolved` or `Whether <clause> is contested`, no
  trailing punctuation. E.g. "Whether egg cholesterol truly causes heart disease is
  unresolved".

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
it should use the **root thesis** or **open-question** label template (a plain
sentence-case clause, or "Whether X is contested"), never the `<Tag>: <clause>`
evidentiary template — that template is reserved for the rare standalone
shared-fact/single-finding node described above.

**Edge** (`schema/edge.schema.json`): `id`, `relation` (`supports` or `depends_on`
only — see below), `from` and `to` — **direction always runs from the more
specific/derived claim to the more general one it relates to**, regardless of
relation type. `provenance` is the source id(s) that assert this specific relation
(may be empty, with `author` set, for an editorial/inferred judgment rather than
something a paper explicitly states).

**Source** (`schema/source.schema.json`): a bibliography entry — `id`, `type`
(`rct | meta_analysis | cohort | review | guideline | news | other`), `title`,
`authors`, `year`, `venue`, `url`. Use real, verifiable citations — a fabricated or
unverified citation defeats the entire point of this tool.

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

1. Create `data/cases/<case_id>/` with `claims.yaml`, `edges.yaml`, `sources.yaml`.
2. Identify the competing root claims (schools of thought) for the topic.
3. Gather real sources first (`sources.yaml`), then build claims and edges from them.
4. Run `python -m src.main validate <case_id>` until clean.

No application code changes needed — the case selector in `app/app.py` picks up any
directory under `data/cases/` automatically.

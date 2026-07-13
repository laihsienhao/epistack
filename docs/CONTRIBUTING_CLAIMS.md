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

**Claim** (`schema/claim.schema.json`): `id`, `case`, `text` (the one-liner shown on
the graph — keep it to a single crisp assertion), `explanation` (optional, longer
markdown shown when the node is expanded), `status` (`draft` or `reviewed` — this is
a curation flag, not a contestedness flag; contestedness is structural, see below),
`tags`, `sources` (ids into `sources.yaml`), `confidence` (leave `null` — reserved for
the Assessment-layer stretch goal), `author`, `created`.

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

from datetime import date

import streamlit as st
import yaml

from src.loader import Graph


def _init_state() -> None:
    if "draft_claims" not in st.session_state:
        st.session_state.draft_claims = []
    if "draft_edges" not in st.session_state:
        st.session_state.draft_edges = []
    if "draft_sources" not in st.session_state:
        st.session_state.draft_sources = []


def render_contribute_form(graph: Graph, author: str = "anonymous") -> None:
    _init_state()

    st.markdown(
        "Propose a new source, claim, or edge for this case. Nothing is written to "
        "the repo automatically — download the YAML below and open a PR to merge it "
        "into `data/cases/%s/`." % graph.case_id
    )

    with st.form("add_source_form", clear_on_submit=True):
        st.markdown("**Add a source**")
        st.caption(
            "Gather real sources first, then build claims from them — see "
            "docs/CONTRIBUTING_CLAIMS.md. Use real, verifiable citations only."
        )
        source_id = st.text_input("Source ID (kebab-case, e.g. author-year-topic)")
        source_title = st.text_input("Title")
        source_type = st.selectbox(
            "Type",
            ["rct", "meta_analysis", "cohort", "review", "guideline", "news", "other"],
            format_func=lambda t: t.replace("_", " ").upper() if t == "rct" else t.replace("_", " ").capitalize(),
        )
        source_authors = st.text_input(
            "Authors — compact \"Surname Initials\" shorthand, comma-separated",
            help='e.g. "Zhong VW, Van Horn L, Cornelis MC" — not a pre-formatted citation. '
            "The detail panel derives a full APA reference from this at render time.",
        )
        source_year = st.number_input("Year", min_value=1900, max_value=date.today().year, step=1, value=date.today().year)
        source_venue = st.text_input("Venue (optional) — \"Journal Name, volume(issue):pages\"")
        source_url = st.text_input("URL (optional)")
        source_funding = st.selectbox(
            "Funding",
            ["industry", "independent", "government", "mixed", "unknown"],
            format_func=lambda f: f.capitalize(),
            help="Base this on the source's own disclosed funding/COI statement — check the "
            "actual paper, never infer from venue or author name alone. Use 'unknown' only "
            "when genuinely undeterminable after checking, not as a shortcut.",
        )
        source_bias_note = st.text_area(
            "Bias note (optional)",
            help="Only fill this in if something concrete and specific is actually disclosed "
            "(e.g. a named funder or conflict) — leave blank otherwise, don't speculate.",
        )
        submitted_source = st.form_submit_button("Add source")
        if submitted_source and source_id and source_title and source_authors:
            st.session_state.draft_sources.append(
                {
                    "id": source_id,
                    "type": source_type,
                    "title": source_title,
                    "authors": source_authors,
                    "year": int(source_year),
                    "venue": source_venue or None,
                    "url": source_url or None,
                    "funding": source_funding,
                    "bias_note": source_bias_note or None,
                }
            )
            st.success(f"Added draft source '{source_id}' — see it in the download below.")

    existing_source_ids = list(graph.sources) + [s["id"] for s in st.session_state.draft_sources]

    with st.form("add_claim_form", clear_on_submit=True):
        st.markdown("**Add a claim**")
        claim_id = st.text_input("Claim ID (kebab-case)")
        text = st.text_area("One-liner (the precise claim)")
        label = st.text_input("Graph label — a genuine <15-word summary, not a truncation")
        explanation = st.text_area("Explanation (optional, markdown)")
        tags = st.text_input("Tags (comma-separated)")
        claim_sources = st.multiselect("Sources", existing_source_ids)
        submitted = st.form_submit_button("Add claim")
        if submitted and claim_id and text and label:
            st.session_state.draft_claims.append(
                {
                    "id": claim_id,
                    "case": graph.case_id,
                    "text": text,
                    "label": label,
                    "explanation": explanation or None,
                    "status": "draft",
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "sources": claim_sources,
                    "confidence": None,
                    "author": author,
                    "created": date.today().isoformat(),
                }
            )
            st.success(f"Added draft claim '{claim_id}' — see it in the download below.")

    existing_ids = list(graph.claims) + [c["id"] for c in st.session_state.draft_claims]
    if existing_ids:
        with st.form("add_edge_form", clear_on_submit=True):
            st.markdown("**Add an edge**")
            edge_id = st.text_input("Edge ID")
            relation = st.selectbox(
                "Relation", ["supports", "depends_on"], format_func=lambda r: r.replace("_", " ")
            )
            from_id = st.selectbox("From (the more specific claim)", existing_ids)
            to_id = st.selectbox("To (the more general claim it relates to)", existing_ids)
            submitted_edge = st.form_submit_button("Add edge")
            if submitted_edge and edge_id:
                st.session_state.draft_edges.append(
                    {
                        "id": edge_id,
                        "relation": relation,
                        "from": from_id,
                        "to": to_id,
                        "provenance": [],
                        "author": author,
                        "created": date.today().isoformat(),
                    }
                )
                st.success(f"Added draft edge '{edge_id}'.")

    if st.session_state.draft_sources or st.session_state.draft_claims or st.session_state.draft_edges:
        st.markdown(
            "**Draft YAML** — append to the case's `sources.yaml` / `claims.yaml` / "
            "`edges.yaml`, then open a PR."
        )
        if st.session_state.draft_sources:
            sources_yaml = yaml.safe_dump(st.session_state.draft_sources, sort_keys=False)
            st.code(sources_yaml, language="yaml")
            st.download_button("Download draft sources.yaml", sources_yaml, file_name="draft_sources.yaml")
        if st.session_state.draft_claims:
            claims_yaml = yaml.safe_dump(st.session_state.draft_claims, sort_keys=False)
            st.code(claims_yaml, language="yaml")
            st.download_button("Download draft claims.yaml", claims_yaml, file_name="draft_claims.yaml")
        if st.session_state.draft_edges:
            edges_yaml = yaml.safe_dump(st.session_state.draft_edges, sort_keys=False)
            st.code(edges_yaml, language="yaml")
            st.download_button("Download draft edges.yaml", edges_yaml, file_name="draft_edges.yaml")

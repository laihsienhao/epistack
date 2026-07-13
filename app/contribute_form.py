from datetime import date

import streamlit as st
import yaml

from src.loader import Graph


def _init_state() -> None:
    if "draft_claims" not in st.session_state:
        st.session_state.draft_claims = []
    if "draft_edges" not in st.session_state:
        st.session_state.draft_edges = []


def render_contribute_form(graph: Graph, author: str = "anonymous") -> None:
    _init_state()

    st.markdown(
        "Propose a new claim or edge for this case. Nothing is written to the "
        "repo automatically — download the YAML below and open a PR to merge it "
        "into `data/cases/%s/`." % graph.case_id
    )

    with st.form("add_claim_form", clear_on_submit=True):
        st.markdown("**Add a claim**")
        claim_id = st.text_input("Claim ID (kebab-case)")
        text = st.text_area("One-liner (the precise claim)")
        label = st.text_input("Graph label — a genuine <15-word summary, not a truncation")
        explanation = st.text_area("Explanation (optional, markdown)")
        tags = st.text_input("Tags (comma-separated)")
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
                    "sources": [],
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

    if st.session_state.draft_claims or st.session_state.draft_edges:
        st.markdown("**Draft YAML** — append to the case's `claims.yaml` / `edges.yaml`, then open a PR.")
        if st.session_state.draft_claims:
            claims_yaml = yaml.safe_dump(st.session_state.draft_claims, sort_keys=False)
            st.code(claims_yaml, language="yaml")
            st.download_button("Download draft claims.yaml", claims_yaml, file_name="draft_claims.yaml")
        if st.session_state.draft_edges:
            edges_yaml = yaml.safe_dump(st.session_state.draft_edges, sort_keys=False)
            st.code(edges_yaml, language="yaml")
            st.download_button("Download draft edges.yaml", edges_yaml, file_name="draft_edges.yaml")

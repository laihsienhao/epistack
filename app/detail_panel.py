import streamlit as st

from src.crux import compute_cruxes
from src.loader import Graph
from src.models import Source


def _format_source(source: Source) -> str:
    parts = [f"**{source.title}**"]
    meta = ", ".join(filter(None, [source.authors, str(source.year), source.venue]))
    if meta:
        parts.append(meta)
    if source.url:
        parts.append(f"[↗ view source]({source.url})")
    return "  \n".join(parts)


def _render_body(graph: Graph, claim_id: str) -> None:
    claim = graph.claims[claim_id]
    crux_for = compute_cruxes(graph).get(claim_id, set())
    is_root = claim_id in graph.roots()
    is_double_crux = len(crux_for) >= 2

    badges = []
    if is_root:
        badges.append("Root thesis")
    if is_double_crux:
        badges.append("Double crux")
    elif crux_for:
        badges.append("Crux")
    if badges:
        st.caption(" &nbsp;·&nbsp; ".join(badges))

    st.markdown(f"#### {claim.text}")

    if crux_for:
        root_texts = [graph.claims[r].label for r in crux_for if r in graph.claims]
        st.warning("**Crux for:** " + " · ".join(root_texts))

    if claim.explanation:
        st.markdown(claim.explanation)

    sources = graph.resolve_sources(claim.sources)
    if sources:
        st.markdown("**References**")
        for source in sources:
            with st.container(border=True):
                st.markdown(_format_source(source))

    incoming = graph.incoming(claim_id)
    outgoing = graph.outgoing(claim_id)
    if incoming or outgoing:
        st.divider()
        col_in, col_out = st.columns(2)
        with col_in:
            if incoming:
                st.markdown("**Points into this claim**")
                for edge in incoming:
                    other = graph.claims.get(edge.from_)
                    if other:
                        bullet = "‣" if edge.relation == "depends_on" else "•"
                        st.markdown(f"{bullet} {other.label}")
        with col_out:
            if outgoing:
                st.markdown("**This claim points into**")
                for edge in outgoing:
                    other = graph.claims.get(edge.to)
                    if other:
                        bullet = "‣" if edge.relation == "depends_on" else "•"
                        st.markdown(f"{bullet} {other.label}")


@st.dialog("Claim details", width="medium")
def _dialog(graph: Graph, claim_id: str) -> None:
    _render_body(graph, claim_id)


def show_node_dialog(graph: Graph, claim_id: str) -> None:
    if claim_id in graph.claims:
        _dialog(graph, claim_id)

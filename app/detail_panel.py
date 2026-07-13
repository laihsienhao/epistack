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
        parts.append(f"[link]({source.url})")
    return " — ".join(parts)


def render_detail(graph: Graph, claim_id: str | None) -> None:
    if claim_id is None or claim_id not in graph.claims:
        st.info("Click a node in the graph to see its full explanation, references, and edges.")
        return

    claim = graph.claims[claim_id]
    crux_for = compute_cruxes(graph).get(claim_id, set())

    st.subheader(claim.text)

    badges = []
    if claim_id in graph.roots():
        badges.append("🏛️ root thesis")
    if len(crux_for) >= 2:
        badges.append("🔑🔑 double crux")
    elif crux_for:
        badges.append("🔑 crux")
    if badges:
        st.caption(" · ".join(badges))

    if claim.explanation:
        st.markdown(claim.explanation)

    sources = graph.resolve_sources(claim.sources)
    if sources:
        st.markdown("**References**")
        for source in sources:
            st.markdown(f"- {_format_source(source)}")

    incoming = graph.incoming(claim_id)
    if incoming:
        st.markdown("**Claims that point into this one**")
        for edge in incoming:
            other = graph.claims.get(edge.from_)
            if other:
                st.markdown(f"- ({edge.relation}) {other.text}")

    outgoing = graph.outgoing(claim_id)
    if outgoing:
        st.markdown("**This claim points into**")
        for edge in outgoing:
            other = graph.claims.get(edge.to)
            if other:
                st.markdown(f"- ({edge.relation}) {other.text}")

    if crux_for:
        root_texts = [graph.claims[r].text for r in crux_for if r in graph.claims]
        st.warning("Crux for: " + "; ".join(root_texts))

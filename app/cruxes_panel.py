import streamlit as st

from src.crux import compute_cruxes
from src.loader import Graph


def render_cruxes_panel(graph: Graph) -> None:
    crux_map = compute_cruxes(graph)
    if not crux_map:
        st.info("No cruxes detected yet — add depends_on edges to mark load-bearing claims.")
        return

    st.markdown(
        "Claims whose falsification would break a necessary condition for a root "
        "thesis, ranked by how many theses they're load-bearing for. "
        "🔑🔑 double cruxes are the highest-value entries — settling them would "
        "move more than one school of thought."
    )

    ranked = sorted(crux_map.items(), key=lambda item: (-len(item[1]), item[0]))
    for claim_id, roots in ranked:
        claim = graph.claims.get(claim_id)
        if claim is None:
            continue
        icon = "🔑🔑" if len(roots) >= 2 else "🔑"
        root_texts = [graph.claims[r].text for r in roots if r in graph.claims]
        with st.expander(f"{icon} {claim.text}"):
            if claim.explanation:
                st.markdown(claim.explanation)
            st.markdown("**Crux for:**")
            for text in root_texts:
                st.markdown(f"- {text}")

import streamlit as st

from src.crux import compute_cruxes
from src.loader import Graph


def render_cruxes_panel(graph: Graph) -> None:
    crux_map = compute_cruxes(graph)
    if not crux_map:
        st.info(
            "No cruxes detected for the current root theses. This can mean the case "
            "hasn't been built out yet — add depends-on edges to mark load-bearing "
            "claims. It can also be a genuine finding rather than a gap: once a thesis "
            "rests on several independently-sufficient pillars (e.g. a broad 'eggs are "
            "unhealthy' claim backed by cholesterol, TMAO, diabetes risk, and food-safety "
            "arguments that don't depend on each other), no single sub-question is "
            "strictly necessary for it anymore — so nothing qualifies as a crux at that "
            "level, even though narrower sub-arguments inside the tree may still have "
            "their own load-bearing cruxes."
        )
        return

    st.markdown(
        "Claims whose falsification would break a necessary condition for a root "
        "thesis, ranked by how many theses they're load-bearing for. "
        "Double cruxes are the highest-value entries — settling them would "
        "move more than one school of thought."
    )

    ranked = sorted(crux_map.items(), key=lambda item: (-len(item[1]), item[0]))
    for claim_id, roots in ranked:
        claim = graph.claims.get(claim_id)
        if claim is None:
            continue
        label = "Double crux" if len(roots) >= 2 else "Crux"
        root_texts = [graph.claims[r].text for r in roots if r in graph.claims]
        with st.expander(f"[{label}] {claim.text}"):
            if claim.explanation:
                st.markdown(claim.explanation)
            st.markdown("**Crux for:**")
            for text in root_texts:
                st.markdown(f"- {text}")

import streamlit as st

from src.crux import compute_cruxes
from src.loader import Graph
from src.research_priorities import research_priorities


def _render_root_cruxes(graph: Graph) -> None:
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
            "their own load-bearing cruxes (see Research priorities below)."
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


def _render_research_priorities(graph: Graph) -> None:
    priorities = research_priorities(graph)
    if not priorities:
        st.info(
            "No research priorities identified — either nothing is a crux for any root "
            "or synthesizing sub-thesis yet, or every such crux is tagged `contextual` "
            "(an apparent conflict that resolves once a variable is specified, not an "
            "open question)."
        )
        return

    st.markdown(
        "Ranked by how many reference points — root theses **and** synthesizing "
        "sub-theses (non-root claims 2+ other claims feed into, so a broadened thesis "
        "doesn't hide a genuinely load-bearing claim just because it's no longer "
        "necessary at the top level) — a claim is load-bearing for, then by how much of "
        "the graph's argument structure routes through them. This is the closest this "
        "tool gets to answering *what's the single most valuable question new research "
        "could resolve?* Claims tagged `contextual` are excluded — an apparent conflict "
        "that resolves once a variable is specified isn't an open question, just an "
        "under-scoped one."
    )

    roots = set(graph.roots())
    for entry in priorities:
        claim = graph.claims.get(entry["claim_id"])
        if claim is None:
            continue
        refs = entry["reference_points"]
        if len(refs) >= 2 and all(r in roots for r in refs):
            label = "Double crux"
        elif len(refs) >= 2:
            label = "Multi-crux"
        else:
            label = "Crux"
        ref_texts = [graph.claims[r].label for r in refs if r in graph.claims]
        with st.expander(f"[{label}, impact {entry['impact']}] {claim.text}"):
            if claim.explanation:
                st.markdown("**What's already known, and what would help resolve this:**")
                st.markdown(claim.explanation)
            else:
                st.caption("No explanation recorded describing what would resolve this.")
            st.markdown("**Load-bearing for:**")
            for text in ref_texts:
                st.markdown(f"- {text}")


def render_cruxes_panel(graph: Graph) -> None:
    st.markdown("#### Root-level cruxes")
    _render_root_cruxes(graph)
    st.divider()
    st.markdown("#### Research priorities")
    _render_research_priorities(graph)

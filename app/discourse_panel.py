import streamlit as st

from src.discourse import topic_coverage, topic_emphasis, topic_label
from src.loader import Graph


def render_discourse_panel(graph: Graph) -> None:
    coverage = topic_coverage(graph)
    emphasis = topic_emphasis(graph)
    if not coverage:
        st.info(
            "No sub-question topics tagged for this case yet. Discourse structure, "
            "which side engages with which sub-question, and where one side "
            "is silent on a topic the other has built out, is derived from `topic:` "
            "tags on claims. Add them to surface this view."
        )
        return

    roots = graph.roots()
    root_text = {r: graph.claims[r].label for r in roots if r in graph.claims}

    shared = {topic: rs for topic, rs in coverage.items() if len(rs) >= 2}
    one_sided = {topic: rs for topic, rs in coverage.items() if len(rs) == 1}

    st.markdown(
        "Which side engages with which sub-question, derived from `topic:` "
        "tags, the same way hierarchy and cruxes are derived from edges rather than "
        "stored directly."
    )

    if shared:
        st.markdown("**Shared sub-questions: both sides engage with these**")
        st.caption(
            "The interesting case: a topic reachable from more than one root means "
            "both sides address it, even if they draw opposite conclusions "
            "from it. That's an *explicit* difference in emphasis. Claim/source counts "
            "below can also reveal an *implicit* one: both sides may technically "
            "cover a topic while one has built it out far more than the other."
        )
        for topic, rs in sorted(shared.items(), key=lambda item: item[0]):
            texts = " · ".join(sorted(root_text.get(r, r) for r in rs))
            with st.expander(f"{topic_label(topic)}, addressed by: {texts}"):
                for r in sorted(rs):
                    counts = emphasis.get(topic, {}).get(r, {"claims": 0, "sources": 0})
                    plural_c = "" if counts["claims"] == 1 else "s"
                    plural_s = "" if counts["sources"] == 1 else "s"
                    st.markdown(
                        f"- {root_text.get(r, r)}: {counts['claims']} claim{plural_c}, "
                        f"{counts['sources']} source{plural_s}"
                    )
    else:
        st.info("No sub-question is currently addressed by more than one side.")

    if one_sided:
        st.markdown("**One-sided sub-questions: only one side has built this out**")
        st.caption(
            "Not automatically a gap: a side's own risk or benefit mechanisms are "
            "naturally one-sided arguments. But it does mean the algorithm can't tell "
            "you whether the other side is silent because the topic doesn't apply to "
            "it, or because it was never engaged with; that distinction still "
            "requires a reader's judgment, not just the graph's structure."
        )
        for topic, rs in sorted(one_sided.items(), key=lambda item: item[0]):
            (only_root,) = rs
            st.markdown(f"- **{topic_label(topic)}**: only {root_text.get(only_root, only_root)}")

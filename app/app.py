import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
for path in (REPO_ROOT, APP_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import streamlit as st  # noqa: E402

import contribute_form  # noqa: E402
import cruxes_panel  # noqa: E402
import detail_panel  # noqa: E402
import discourse_panel  # noqa: E402
import graph_view  # noqa: E402
import zoom_controls  # noqa: E402
from src.discourse import topic_label  # noqa: E402
from src.loader import list_cases, load_case  # noqa: E402
from src.validate import validate_case  # noqa: E402

st.set_page_config(page_title="Epistemic Claim Graph", layout="wide")

st.markdown(
    """
    <style>
    div[data-testid="stMainBlockContainer"] {
        padding-left: 32px;
        padding-right: 32px;
    }
    /* Streamlit derives this backdrop's default color from the app's own
       (warm, cream/tan) theme tokens rather than a neutral gray, so it reads
       as a strong yellow/tan wash instead of a normal modal scrim -- pin it
       to a fixed neutral dark tint instead, independent of the page theme. */
    div[data-testid="stDialog"] {
        background-color: rgba(17, 17, 17, 0.35) !important;
    }
    div[data-testid="stDialog"] > div {
        background-color: rgba(255, 255, 255, 0.97) !important;
        backdrop-filter: blur(10px);
    }
    @media (prefers-color-scheme: dark) {
        div[data-testid="stDialog"] > div {
            background-color: rgba(14, 17, 23, 0.97) !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Epistemic claim graph")
st.caption(
    "Structure layer of the epistemic stack — claims as nodes, \"supports\" and "
    "\"depends on\" as edges. Hierarchy, sides, and cruxes are all derived from the "
    "graph, never stored."
)

cases = list_cases()
if not cases:
    st.error("No cases found under data/cases/.")
    st.stop()

default_index = cases.index("eggs") if "eggs" in cases else 0

bar = st.columns([1.1, 2, 1.8, 1.2, 1])
with bar[0]:
    case_id = st.selectbox("Case", cases, index=default_index)

errors = validate_case(case_id)
if errors:
    st.error(f"{len(errors)} validation error(s) in this case")
    for err in errors:
        st.markdown(f"- {err}")
    st.stop()

graph = load_case(case_id)

# The neutral question a case explores -- distinct from the root claims,
# which are each side's *answer* to it, not the shared question itself.
# Authored per-case (data/cases/<id>/case.yaml), not derived: unlike
# hierarchy/cruxes/coverage, there's no mechanical way to produce "What are
# the health impacts of eggs as a human food source?" from "Eggs are
# healthy" and "Eggs are unhealthy" alone.
st.markdown(f"<div style='font-size:1.15em; margin-bottom:0.5em'>{graph.question}</div>", unsafe_allow_html=True)

all_topics = sorted({t for claim in graph.claims.values() for t in claim.tags if t.startswith("topic:")})

with bar[1]:
    search_query = st.text_input("Search claim text")
with bar[2]:
    topic_filter = (
        st.multiselect("Filter by topic", all_topics, format_func=topic_label) if all_topics else []
    )
with bar[3]:
    st.markdown("<div style='height: 1.7em'></div>", unsafe_allow_html=True)
    show_only_cruxes = st.checkbox("Show only cruxes", value=False)
with bar[4]:
    st.markdown("<div style='height: 1.7em'></div>", unsafe_allow_html=True)
    with st.popover("Legend"):
        roots = sorted(graph.roots())
        hues = graph_view._root_hues(roots)
        st.markdown("**Sides**")
        for root in roots:
            claim = graph.claims[root]
            st.markdown(
                f"<span style='color:{hues[root]}'>⬤</span> {claim.text}",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<span style='color:{graph_view.NEUTRAL_FILL}'>⬤</span> Shared / neutral "
            "(reachable from more than one side)",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**Crux status (node border)**")
        st.markdown(
            "Crux (amber border) · Double crux (black border). Root theses "
            "render as the larger circles."
        )
        st.markdown("---")
        st.markdown(
            "**Edges** — thin gray = supports; thick amber = depends-on; "
            "dashed = no direct source citation (editorial judgment)."
        )

tab_graph, tab_cruxes, tab_coverage, tab_contribute = st.tabs(["Graph", "Cruxes", "Coverage", "Contribute"])

with tab_graph:
    zoom_controls.render_zoom_controls()
    # st.context.theme.type reflects the browser's actual active theme
    # ("light"/"dark"/None) -- needed because the in-canvas question node
    # (graph_view.py) has no fill color of its own to derive text contrast
    # from, unlike every other node.
    dark_mode = st.context.theme.type == "dark"
    selected = graph_view.render_graph(graph, search_query, show_only_cruxes, topic_filter, dark_mode)

    if selected and selected != st.session_state.get("last_clicked_node"):
        st.session_state.last_clicked_node = selected
        detail_panel.show_node_dialog(graph, selected)
    elif not selected:
        st.session_state.last_clicked_node = None

    st.caption("Click a node in the graph to see its full explanation, references, and edges.")

with tab_cruxes:
    cruxes_panel.render_cruxes_panel(graph)

with tab_coverage:
    discourse_panel.render_discourse_panel(graph)

with tab_contribute:
    contribute_form.render_contribute_form(graph)

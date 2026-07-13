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
import graph_view  # noqa: E402
from src.loader import list_cases, load_case  # noqa: E402
from src.validate import validate_case  # noqa: E402

st.set_page_config(page_title="Epistemic Claim Graph", layout="wide")

st.title("Epistemic Claim Graph")
st.caption(
    "Structure layer of the epistemic stack — claims as nodes, supports/depends_on "
    "as edges. Hierarchy, shared ground-truths, and cruxes are all derived from the "
    "graph, never stored."
)

cases = list_cases()
if not cases:
    st.error("No cases found under data/cases/.")
    st.stop()

default_index = cases.index("eggs") if "eggs" in cases else 0
case_id = st.sidebar.selectbox("Case", cases, index=default_index)

errors = validate_case(case_id)
if errors:
    st.sidebar.error(f"{len(errors)} validation error(s) in this case")
    for err in errors:
        st.sidebar.markdown(f"- {err}")
    st.stop()

graph = load_case(case_id)

st.sidebar.markdown("---")
all_tags = sorted({tag for claim in graph.claims.values() for tag in claim.tags})
tag_filter = set(st.sidebar.multiselect("Filter by tag", all_tags))
search_query = st.sidebar.text_input("Search claim text")
show_only_cruxes = st.sidebar.checkbox("Show only cruxes", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "🏛️ root thesis · 🔑 crux · 🔑🔑 double crux\n\n"
    "Shared ground-truth claims (reachable from more than one root) render with a "
    "light fill. `depends_on` edges render thicker/amber; `supports` edges are thin."
)

tab_graph, tab_cruxes, tab_contribute = st.tabs(["Graph", "Cruxes", "Contribute"])

with tab_graph:
    col_graph, col_detail = st.columns([2, 1])
    with col_graph:
        selected = graph_view.render_graph(graph, tag_filter, search_query, show_only_cruxes)
    with col_detail:
        detail_panel.render_detail(graph, selected)

with tab_cruxes:
    cruxes_panel.render_cruxes_panel(graph)

with tab_contribute:
    contribute_form.render_contribute_form(graph)

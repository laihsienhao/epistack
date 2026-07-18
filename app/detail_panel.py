import re
from typing import Optional

import streamlit as st

from src.crux import compute_cruxes
from src.discourse import topic_label
from src.ingestion import shared_authorship
from src.loader import Graph
from src.models import Source

# `sources.yaml` stores authors as a compact "Surname Initials" shorthand
# (e.g. "Zhong VW, Van Horn L") rather than pre-formatted APA -- like the
# graph's structure, the citation is derived at render time, not stored.
_PERSON_RE = re.compile(
    r"^(?P<surname>[A-Za-z][\w'\-]*(?:\s[A-Za-z][\w'\-]*)*?)\s+"
    r"(?P<initials>[A-Z]{1,4})"
    r"(?:\s+(?P<suffix>Jr\.?|Sr\.?|II|III|IV))?$"
)


def _format_person(token: str) -> Optional[str]:
    match = _PERSON_RE.match(token.strip())
    if not match:
        return None
    formatted = f"{match.group('surname')}, {'. '.join(match.group('initials'))}."
    if match.group("suffix"):
        formatted += f", {match.group('suffix')}"
    return formatted


def _format_authors_apa(authors: str) -> str:
    authors = authors.strip()
    if not authors or authors.upper() == "N/A":
        return ""
    # Drop a trailing organizational parenthetical (e.g. "Merschel M
    # (American Heart Association News)") -- the venue field already names
    # the organization, so it isn't lost.
    authors = re.sub(r"\s*\([^)]*\)\s*$", "", authors).strip()
    tokens = [t.strip() for t in authors.split(",") if t.strip()]
    has_et_al = bool(tokens) and tokens[-1].lower().rstrip(".") == "et al"
    if has_et_al:
        tokens = tokens[:-1]
    formatted = [_format_person(t) for t in tokens]
    if not tokens or any(f is None for f in formatted):
        # Doesn't parse as a person list -- an organizational author, used
        # verbatim (already in correct form, e.g. "U.S. Food and Drug
        # Administration").
        return authors if authors.endswith(".") else authors + "."
    if has_et_al:
        return ", ".join(formatted) + ", et al."
    if len(formatted) == 1:
        return formatted[0]
    return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def _venue_to_apa(venue: str) -> str:
    # "Journal, 321(11):1081-1095" -> "Journal, 321(11), 1081-1095" --
    # the source data uses a "vol(issue):pages" shorthand; APA separates
    # volume/issue from the page range with a comma, not a colon.
    return re.sub(r"(\d\)?):(\w)", r"\1, \2", venue)


# Study-design type already existed on Source but was never rendered anywhere
# -- a quick, independent win alongside the funding badge below.
_TYPE_LABELS = {
    "rct": "RCT",
    "meta_analysis": "Meta-analysis",
    "cohort": "Cohort study",
    "review": "Review",
    "guideline": "Guideline",
    "news": "News",
    "other": "Other",
}

# Plain factual labels, not a quality score -- this is adversarial-robustness
# transparency (making a source's origin visible), not Assessment-layer
# scoring, so deliberately no color-coding implying "this source is weaker."
_FUNDING_LABELS = {
    "industry": "Industry-funded",
    "independent": "Independently funded",
    "government": "Government-funded",
    "mixed": "Mixed funding",
    "unknown": "Funding unknown",
}

# Distinct from every other color track (side hues, crux amber/black,
# neutral sienna) -- red vs. teal maps to the actual distinction:
# `contested` is a live, unresolved dispute (hot/alarm-like); `contextual` reads
# as resolved-once-scoped (cool/calm). Unlike the graph canvas's node fills
# (see CLAUDE.md's "Contested/contextual claims currently have NO distinct
# visual treatment" -- that history is about the canvas specifically, tried
# and reverted twice), this is popup badge text, not a new graph-level
# visual channel, so it's a different, lower-risk surface for the same
# underlying distinction.
_CONTESTED_COLOR = "#c0392b"  # red
_CONTEXTUAL_COLOR = "#3d7a6e"  # cool teal


def _format_citation_apa(source: Source) -> str:
    author_part = _format_authors_apa(source.authors)
    year_part = f"({source.year})."
    citation = f"{author_part} {year_part}".strip() if author_part else year_part
    citation += f" {source.title}."
    if source.venue:
        citation += f" *{_venue_to_apa(source.venue)}*."
    return citation


def _render_source_card(source: Source) -> None:
    # Year is pulled out of the citation body and bolded alongside the title
    # -- scanning a reverse-chronological list of cards for "when" shouldn't
    # require reading each full APA citation to find it. Metadata (type/
    # funding/bias-note) stays in st.caption -- smaller, muted text -- so it
    # reads as annotation *about* the citation rather than competing on equal
    # visual footing with the citation itself.
    with st.container(border=True):
        st.markdown(f"**{source.year} — {source.title}**")
        badges = [_TYPE_LABELS.get(source.type, source.type), _FUNDING_LABELS.get(source.funding, source.funding)]
        st.caption(" · ".join(badges))
        st.markdown(_format_citation_apa(source))
        if source.bias_note:
            st.caption(f"‣ {source.bias_note}")
        if source.url:
            st.markdown(f"[↗ view source]({source.url})")


def _render_edge_column(graph: Graph, edges, other_id_fn, header: str) -> None:
    if not edges:
        st.caption("None recorded.")
        return
    st.markdown(f"**{header}**")
    for edge in edges:
        other = graph.claims.get(other_id_fn(edge))
        if other:
            bullet = "‣" if edge.relation == "depends_on" else "•"
            st.markdown(f"{bullet} {other.label}")


def _render_body(graph: Graph, claim_id: str) -> None:
    claim = graph.claims[claim_id]
    crux_for = compute_cruxes(graph).get(claim_id, set())
    is_root = claim_id in graph.roots()
    is_double_crux = len(crux_for) >= 2

    # --- Always-visible header: status at a glance, no scrolling/clicking ---
    badges = []
    if is_root:
        badges.append("Root thesis")
    if is_double_crux:
        badges.append("Double crux")
    elif crux_for:
        badges.append("Crux")
    if claim.status == "draft":
        badges.append("Draft")
    if badges:
        st.caption(" &nbsp;·&nbsp; ".join(badges))

    # Rendered separately from the plain badges above (not folded into the
    # same muted caption line) so it's the one status a reader can't miss --
    # bold, full-opacity, colored by which of the two it is, rather than
    # competing for attention at the same visual weight as "Draft."
    if "contested" in claim.tags:
        st.markdown(f"<span style='color:{_CONTESTED_COLOR}; font-weight:700'>Contested</span>", unsafe_allow_html=True)
    elif "contextual" in claim.tags:
        st.markdown(f"<span style='color:{_CONTEXTUAL_COLOR}; font-weight:700'>Contextual</span>", unsafe_allow_html=True)

    topics = [t for t in claim.tags if t.startswith("topic:")]
    if topics:
        st.caption("Topics: " + " · ".join(topic_label(t) for t in sorted(topics)))

    st.markdown(f"#### {claim.text}")

    if crux_for:
        root_texts = [graph.claims[r].label for r in crux_for if r in graph.claims]
        st.warning("**Crux for:** " + " · ".join(root_texts))

    # --- Everything else, grouped into tabs instead of one long scroll ---
    # Reverse-chronological (newest first), not YAML declaration order --
    # leads with the most recent evidence, same convention as a reference
    # list a reader would expect, while still reading as the evidentiary
    # timeline behind a claim's current shape -- a small honest partial
    # answer to tracking structure over time (the graph itself still isn't
    # versioned, but the evidence behind a claim is now orderable).
    sources = sorted(graph.resolve_sources(claim.sources), key=lambda s: s.year, reverse=True)
    incoming = graph.incoming(claim_id)
    outgoing = graph.outgoing(claim_id)

    tab_overview, tab_evidence, tab_connections = st.tabs(
        ["Overview", f"Evidence ({len(sources)})", f"Connections ({len(incoming) + len(outgoing)})"]
    )

    with tab_overview:
        if claim.explanation:
            st.markdown(claim.explanation)
        else:
            st.caption("No further explanation recorded for this claim.")

    with tab_evidence:
        if sources:
            for a, b, surnames in shared_authorship(sources):
                names = ", ".join(s.title() for s in surnames)
                st.info(
                    f"“{a.title}” and “{b.title}” list author surname(s) in "
                    f"common ({names}) — worth checking whether this is independent "
                    "corroboration or the same research group before treating them as two."
                )
            for source in sources:
                _render_source_card(source)
        else:
            st.caption("No sources recorded for this claim.")

    with tab_connections:
        col_in, col_out = st.columns(2)
        with col_in:
            _render_edge_column(graph, incoming, lambda e: e.from_, "Points into this claim")
        with col_out:
            _render_edge_column(graph, outgoing, lambda e: e.to, "This claim points into")


@st.dialog("Claim details", width="medium")
def _dialog(graph: Graph, claim_id: str) -> None:
    _render_body(graph, claim_id)


def show_node_dialog(graph: Graph, claim_id: str) -> None:
    if claim_id in graph.claims:
        _dialog(graph, claim_id)

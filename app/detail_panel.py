import re
from typing import Optional

import streamlit as st

from src.crux import compute_cruxes
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


def _format_citation_apa(source: Source) -> str:
    author_part = _format_authors_apa(source.authors)
    year_part = f"({source.year})."
    citation = f"{author_part} {year_part}".strip() if author_part else year_part
    citation += f" {source.title}."
    if source.venue:
        citation += f" *{_venue_to_apa(source.venue)}*."
    return citation


def _format_source(source: Source) -> str:
    parts = [f"**{source.title}**", _format_citation_apa(source)]
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

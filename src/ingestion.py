import re

from .models import Source

# Same "Surname Initials" shorthand app/detail_panel.py's APA formatter
# parses, but this only needs (surname, initials) as a comparison key -- not
# a rendered citation -- so it's a separate, simpler regex rather than a
# cross-layer import from app/ into src/.
_PERSON_RE = re.compile(
    r"^(?P<surname>[A-Za-z][\w'\-]*(?:\s[A-Za-z][\w'\-]*)*?)\s+(?P<initials>[A-Z]{1,4})(?:\s+(?:Jr\.?|Sr\.?|II|III|IV))?$"
)


def _extract_authors(authors: str) -> list[tuple[str, str]]:
    """Parse a compact "Surname Initials" author string into (surname,
    initials) pairs, lowercased surnames."""
    authors = re.sub(r"\s*\([^)]*\)\s*$", "", authors.strip()).strip()
    parsed: list[tuple[str, str]] = []
    for token in authors.split(","):
        token = token.strip()
        if not token or token.lower().rstrip(".") == "et al":
            continue
        match = _PERSON_RE.match(token)
        if match:
            parsed.append((match.group("surname").strip().lower(), match.group("initials")))
    return parsed


def _initials_compatible(a: str, b: str) -> bool:
    # "Schlosser W" and "Schlosser WD" are almost certainly the same person
    # recorded with/without a middle initial across two papers -- a strict
    # equality check would miss that real match. But "Zhao L" and "Zhao B"
    # are almost certainly two different people who happen to share a common
    # surname -- surname-only matching (an earlier version of this function)
    # actually produced exactly that false positive on the real eggs corpus.
    # Prefix-compatibility catches the first case without falling for the
    # second.
    return a == b or a.startswith(b) or b.startswith(a)


def shared_authorship(sources: list[Source]) -> list[tuple[Source, Source, list[str]]]:
    """Flag pairs within a set of sources (e.g. one claim's evidence list)
    that list the same author (matched on surname + initials-compatibility,
    not surname alone) -- one entry per pair, carrying every surname they
    share, not one entry per shared name.

    Ingestion-layer duplicate/overlap detection that doubles as an
    Assessment-layer signal: a claim backed by several sources reads as
    stronger corroboration than one source, but if two of those sources
    share an author (or a whole research group), they may not be
    independent -- worth a reader's attention, not proof either way. This is
    still plain string matching on the compact "Surname Initials" field, not
    a verified author-identity check, so it's a hint to look closer, not an
    assertion that two sources are the same lab's work -- a sufficiently
    common surname+initials combination could still coincidentally match two
    different people.
    """
    flagged: list[tuple[Source, Source, list[str]]] = []
    parsed = {s.id: _extract_authors(s.authors) for s in sources}
    for i, a in enumerate(sources):
        for b in sources[i + 1 :]:
            shared = sorted(
                {
                    surname_a
                    for surname_a, initials_a in parsed[a.id]
                    for surname_b, initials_b in parsed[b.id]
                    if surname_a == surname_b and _initials_compatible(initials_a, initials_b)
                }
            )
            if shared:
                flagged.append((a, b, shared))
    return flagged

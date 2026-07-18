import re

from .models import Source

# Same "Surname Initials" shorthand app/detail_panel.py's APA formatter
# parses, but this only needs the surname as a comparison key -- not a
# rendered citation -- so it's a separate, simpler regex rather than a
# cross-layer import from app/ into src/.
_PERSON_RE = re.compile(r"^(?P<surname>[A-Za-z][\w'\-]*(?:\s[A-Za-z][\w'\-]*)*?)\s+[A-Z]{1,4}(?:\s+(?:Jr\.?|Sr\.?|II|III|IV))?$")


def _extract_surnames(authors: str) -> set[str]:
    authors = re.sub(r"\s*\([^)]*\)\s*$", "", authors.strip()).strip()
    surnames: set[str] = set()
    for token in authors.split(","):
        token = token.strip()
        if not token or token.lower().rstrip(".") == "et al":
            continue
        match = _PERSON_RE.match(token)
        if match:
            surnames.add(match.group("surname").strip().lower())
    return surnames


def shared_authorship(sources: list[Source]) -> list[tuple[Source, Source, list[str]]]:
    """Flag pairs within a set of sources (e.g. one claim's evidence list)
    that list an author surname in common -- one entry per pair, carrying
    every surname they share, not one entry per shared name.

    Ingestion-layer duplicate/overlap detection that doubles as an
    Assessment-layer signal: a claim backed by several sources reads as
    stronger corroboration than one source, but if two of those sources
    share an author (or a whole research group), they may not be
    independent -- worth a reader's attention, not proof either way. This is
    plain surname string-matching on the compact "Surname Initials" field,
    not a verified author-identity check, so it's a hint to look closer, not
    an assertion that two sources are the same lab's work.
    """
    flagged: list[tuple[Source, Source, list[str]]] = []
    surnames = {s.id: _extract_surnames(s.authors) for s in sources}
    for i, a in enumerate(sources):
        for b in sources[i + 1 :]:
            shared = sorted(surnames[a.id] & surnames[b.id])
            if shared:
                flagged.append((a, b, shared))
    return flagged

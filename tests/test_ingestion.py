from src.ingestion import shared_authorship
from src.models import Source


def _source(id_, authors, title=None):
    return Source(
        id=id_,
        type="rct",
        title=title or id_,
        authors=authors,
        year=2020,
        funding="unknown",
    )


def test_flags_sources_sharing_an_author_surname():
    a = _source("a", "Hazen SL, Tang WHW")
    b = _source("b", "Wilcox J, Hazen SL")
    flagged = shared_authorship([a, b])
    assert len(flagged) == 1
    src_a, src_b, surnames = flagged[0]
    assert {src_a.id, src_b.id} == {"a", "b"}
    assert surnames == ["hazen"]


def test_one_note_per_pair_even_with_multiple_shared_surnames():
    a = _source("a", "Tang WHW, Fu X, Hazen SL")
    b = _source("b", "Wilcox J, Fu X, Hazen SL")
    flagged = shared_authorship([a, b])
    assert len(flagged) == 1
    _a, _b, surnames = flagged[0]
    assert surnames == ["fu", "hazen"]


def test_no_flag_when_no_shared_author():
    a = _source("a", "Zhong VW, Van Horn L")
    b = _source("b", "Astrup A, Magkos F")
    assert shared_authorship([a, b]) == []


def test_et_al_and_org_authors_do_not_crash_or_false_match():
    a = _source("a", "Drouin-Chartier JP, et al.")
    b = _source("b", "U.S. Food and Drug Administration")
    c = _source("c", "N/A")
    assert shared_authorship([a, b, c]) == []


def test_no_self_pairing_and_no_duplicate_pairs():
    a = _source("a", "Hazen SL")
    b = _source("b", "Hazen SL")
    c = _source("c", "Hazen SL")
    flagged = shared_authorship([a, b, c])
    # 3 sources, all sharing one surname -> 3 distinct pairs, not 6+ duplicates
    assert len(flagged) == 3


def test_same_surname_different_initials_is_not_flagged():
    # regression test: an earlier surname-only version of this function
    # produced exactly this false positive on the real eggs corpus --
    # "Zhao L" and "Zhao B" are almost certainly two different people.
    a = _source("a", "Zhao L, Zhong VW")
    b = _source("b", "Zhao B, Gan L")
    assert shared_authorship([a, b]) == []


def test_prefix_compatible_initials_are_flagged():
    # "Schlosser W" and "Schlosser WD" are almost certainly the same person
    # recorded with/without a middle initial -- prefix-compatible, not an
    # exact match, so this must not require strict equality.
    a = _source("a", "Ebel E, Schlosser W")
    b = _source("b", "Schroeder CM, Schlosser WD")
    flagged = shared_authorship([a, b])
    assert len(flagged) == 1
    _a, _b, surnames = flagged[0]
    assert surnames == ["schlosser"]

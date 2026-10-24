from datetime import datetime, timedelta, timezone

import pytest

from projects.intermediate.url_shortener.codes import ALPHABET, InvalidURLError, code_for_id, decode, encode, normalize_url, validate_alias
from projects.intermediate.url_shortener.shortener import AliasTakenError, LinkNotFoundError, Shortener


@pytest.mark.parametrize("n", [0, 1, 61, 62, 125, 3843, 10**12])
def test_base62_round_trip(n):
    assert decode(encode(n)) == n


def test_known_encodings():
    assert encode(0) == "0" and encode(61) == "Z" and encode(62) == "10" and code_for_id(1) == "101"
    assert len(set(ALPHABET)) == 62


@pytest.mark.parametrize("raw, url", [("example.com", "https://example.com/"), ("HTTP://Example.COM/A?b=1", "http://example.com/A?b=1"),
                                      ("localhost:5000/x", "https://localhost:5000/x")])
def test_normalize_url(raw, url):
    assert normalize_url(raw) == url


@pytest.mark.parametrize("bad", ["", "ftp://example.com", "javascript:alert(1)", "not a url", "nodot", "x" * 3000])
def test_invalid_urls(bad):
    with pytest.raises(InvalidURLError):
        normalize_url(bad)


@pytest.mark.parametrize("alias", ["ab", "has space", "admin", "x" * 40])
def test_invalid_aliases(alias):
    with pytest.raises(ValueError):
        validate_alias(alias)


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


@pytest.fixture
def svc(tmp_path):
    clock = FakeClock()
    s = Shortener(tmp_path / "links.db", clock=clock)
    s.clock_obj = clock
    return s


def test_shorten_and_resolve(svc):
    link = svc.shorten("python.org")
    assert link.code == "101" and link.url == "https://python.org/"
    assert svc.resolve("101") == "https://python.org/"
    assert svc.shorten("https://python.org/").code == "101"          # same URL → same code


def test_custom_alias(svc):
    assert svc.shorten("python.org", alias="pydocs").code == "pydocs"
    with pytest.raises(AliasTakenError):
        svc.shorten("example.com", alias="pydocs")


def test_unknown_code(svc):
    with pytest.raises(LinkNotFoundError):
        svc.resolve("nope")


def test_stats_count_clicks_per_day_and_referrer(svc):
    svc.shorten("python.org")
    svc.resolve("101", "https://news.ycombinator.com")
    svc.clock_obj.now += timedelta(days=1)
    svc.resolve("101")
    svc.resolve("101")
    st = svc.stats("101")
    assert st.link.clicks == 3
    assert st.clicks_by_day == [("2026-05-01", 1), ("2026-05-02", 2)]
    assert st.top_referrers[0] == ("direct", 2)


def test_delete_removes_link_and_clicks(svc):
    svc.shorten("python.org")
    svc.resolve("101")
    svc.delete("101")
    assert svc.all_links() == []
    with pytest.raises(LinkNotFoundError):
        svc.delete("101")

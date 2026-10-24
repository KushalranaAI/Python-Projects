---
title: URL Shortener
order: 3
icon: 🔗
time: 3-4 hours
summary: Turn long links into short codes like /1Ab, redirect visitors and count clicks per day. Covers base conversion, URL validation, HTTP redirects and SQL joins.
python_skills:
  - divmod and base conversion (base 62)
  - urllib.parse - urlsplit / urlunsplit
  - sqlite3 with UNIQUE constraints, LEFT JOIN, foreign keys
  - datetime with time zones
  - HTTP status codes (302 redirect, 404)
oop_concepts:
  - A service class that owns its storage
  - Injecting a clock (a callable object) for testable time
  - Custom exceptions per failure
  - Frozen dataclasses for results (Link, LinkStats)
clean_code:
  - Validate and normalise input at the boundary (URL, alias)
  - Idempotent operations - shortening the same URL twice returns the same link
  - Reserved words and length limits
  - A fake clock class in tests instead of sleeping
features:
  - Short codes generated from the database id (base 62), or a custom alias
  - Redirect endpoint that counts every click
  - Per-link stats - clicks per day and top referrers
  - Accepts "example.com" and normalises to https://example.com/
architecture: |
  classDiagram
    class codes {
      <<module>>
      +encode(n) str
      +decode(code) int
      +code_for_id(id) str
      +normalize_url(raw) str
      +validate_alias(alias) str
    }
    class Shortener {
      -db_path str
      -clock callable
      +shorten(url, alias) Link
      +resolve(code, referrer) str
      +all_links() list~Link~
      +stats(code) LinkStats
      +delete(code)
    }
    class Link {
      <<frozen>>
      +id int
      +code str
      +url str
      +custom bool
      +created_at datetime
      +clicks int
    }
    class LinkStats {
      +link Link
      +clicks_by_day list
      +top_referrers list
    }
    Shortener ..> codes : uses
    Shortener ..> Link
    Shortener ..> LinkStats
flow: |
  sequenceDiagram
    participant B as Browser
    participant W as web.py /go/1Ab
    participant S as Shortener
    participant DB as SQLite
    B->>W: GET /go/1Ab
    W->>S: resolve("1Ab", referrer)
    S->>DB: SELECT url WHERE code = ?
    S->>DB: INSERT INTO clicks
    S-->>W: https://docs.python.org/...
    W-->>B: 302 Found, Location: https://docs.python.org/...
    B->>B: follows the redirect
steps:
  - title: Base 62 by hand
    files: [codes.py, tests/test_shortener.py]
    body: |
      Writing a number in base 62 works exactly like base 2 or base 10: `divmod(n, 62)` gives the next digit and the rest.
      Codes come from the database **id**, so they're unique by construction. Test the round trip `decode(encode(n)) == n`
      for edge values (0, 61, 62).
  - title: Validate and normalise URLs
    files: [codes.py]
    body: |
      `urlsplit` breaks a URL into scheme, host, path… We add `https://` when missing, lowercase the host, and reject
      `javascript:` and `ftp:`. A shortener that redirects to `javascript:` would be a security hole.
  - title: Design the tables
    files: [shortener.py]
    body: |
      `links.code` is `UNIQUE`, so the database itself prevents duplicate aliases. `clicks` references `links` with
      `ON DELETE CASCADE`, so deleting a link deletes its clicks (with `PRAGMA foreign_keys = ON`).
  - title: The Shortener service
    files: [shortener.py]
    body: |
      `shorten` returns the existing link for a URL it has seen (idempotent), and checks custom aliases. The code depends
      on the id, so we `INSERT` first and `UPDATE` the code using `cursor.lastrowid`. `all_links` uses a `LEFT JOIN … GROUP BY`
      to count clicks in one query.
  - title: Control time in tests
    files: [shortener.py, tests/test_shortener.py]
    body: |
      `Shortener(db, clock=...)` takes any callable returning a datetime. Tests pass a `FakeClock` object (it defines
      `__call__`) and move it forward a day to test per-day statistics without waiting.
  - title: Redirects and stats pages
    files: [web.py, templates/url_shortener/index.html, templates/url_shortener/stats.html]
    body: |
      `/go/<code>` answers **302 Found** with a `Location` header. (A 301 would be cached by browsers, so later clicks
      wouldn't reach us to be counted.) Unknown codes get a proper **404**.
exercises:
  - Add **expiry dates** - links stop working after a chosen date (return 410 Gone).
  - Make codes **non-sequential** so people can't guess other links (hint - multiply the id by a large prime modulo 62⁶).
  - Generate a **QR code** for each short link with the `qrcode` package.
  - Add a **JSON API** (`POST /api/links`) and write a test using Flask's test client.
---

## How many links fit?

| Code length | Possible codes (62ⁿ) |
|---|---|
| 3 | 238,328 |
| 4 | 14,776,336 |
| 6 | 56,800,235,584 |
| 7 | 3,521,614,606,208 |

Each extra character multiplies capacity by 62. Real shorteners start at 6-7 characters.

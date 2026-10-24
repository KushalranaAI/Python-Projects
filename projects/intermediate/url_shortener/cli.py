"""Terminal interface:  shorten <url> [--alias x] | open <code> | list | stats <code>"""

from __future__ import annotations

import argparse

from projects.ui_kit import data_path

from .shortener import LinkNotFoundError, Shortener


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="shorty")
    sub = parser.add_subparsers(dest="command")
    s = sub.add_parser("shorten")
    s.add_argument("url")
    s.add_argument("--alias")
    sub.add_parser("open").add_argument("code")
    sub.add_parser("stats").add_argument("code")
    sub.add_parser("list")
    args = parser.parse_args(argv)
    service = Shortener(data_path("links.db"))
    try:
        if args.command == "shorten":
            link = service.shorten(args.url, args.alias)
            print(f"/{link.code}  →  {link.url}")
        elif args.command == "open":
            print(service.resolve(args.code, referrer="cli"))
        elif args.command == "stats":
            st = service.stats(args.code)
            print(f"{st.link.url}: {st.link.clicks} clicks")
            for day, n in st.clicks_by_day:
                print(f"  {day} {'█' * n} {n}")
        else:
            for link in service.all_links():
                print(f"  /{link.code:<10} {link.clicks:>4} clicks  {link.url}")
    except (ValueError, LinkNotFoundError) as error:
        raise SystemExit(f"error: {error}")


if __name__ == "__main__":
    main()

"""Terminal interface:  generate | passphrase | check"""

from __future__ import annotations

import argparse
import getpass

from .toolkit import PasswordGenerator, PasswordPolicy, check_strength


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="passwords")
    sub = parser.add_subparsers(dest="command", required=False)
    gen = sub.add_parser("generate")
    gen.add_argument("-l", "--length", type=int, default=16)
    gen.add_argument("-n", "--count", type=int, default=5)
    gen.add_argument("--no-symbols", action="store_true")
    gen.add_argument("--no-ambiguous", action="store_true")
    phrase = sub.add_parser("passphrase")
    phrase.add_argument("-w", "--words", type=int, default=5)
    sub.add_parser("check")
    args = parser.parse_args(argv)
    generator = PasswordGenerator()

    if args.command == "passphrase":
        print(generator.passphrase(args.words), f"(~{generator.passphrase_entropy(args.words):.0f} bits)")
    elif args.command == "check":
        report = check_strength(getpass.getpass("Password to check (hidden): "))
        print(f"{report.label} - ~{report.entropy_bits} bits, cracked in ~{report.crack_time}")
        for line in report.warnings + report.suggestions:
            print(" •", line)
    else:
        policy = PasswordPolicy(length=getattr(args, "length", 16), symbols=not getattr(args, "no_symbols", False),
                                exclude_ambiguous=getattr(args, "no_ambiguous", False))
        try:
            for _ in range(getattr(args, "count", 5)):
                print(generator.password(policy))
        except ValueError as error:
            raise SystemExit(f"error: {error}")
        print(f"(~{policy.entropy_bits:.0f} bits each)")


if __name__ == "__main__":
    main()

import argparse
import sys

from .validate import validate_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.main")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a case's claim graph")
    validate_parser.add_argument("case_id")

    args = parser.parse_args(argv)

    if args.command == "validate":
        errors = validate_case(args.case_id)
        if errors:
            print(f"case '{args.case_id}' has {len(errors)} error(s):")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"case '{args.case_id}' is valid.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

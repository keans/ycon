"""Command-line interface for ycon."""

import argparse
import json

from ycon import __version__, compare_files, load, resolve_to_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ycon")
    parser.add_argument(
        "--version", action="version", version=f"ycon {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_defaults_args(subparser):
        subparser.add_argument("--defaults")
        subparser.add_argument(
            "--strict",
            action="store_true",
            help="Raise an error if the config has a key absent from "
            "--defaults",
        )

    show = sub.add_parser("show", help="Load a config and print it as JSON")
    show.add_argument("path")
    add_defaults_args(show)

    resolve = sub.add_parser(
        "resolve", help="Resolve a config and write it out as plain YAML"
    )
    resolve.add_argument("path")
    resolve.add_argument("-o", "--output", required=True)
    add_defaults_args(resolve)
    resolve.add_argument(
        "--keep-aliases",
        action="store_true",
        help="Keep shared values as YAML anchors/aliases in the output",
    )

    diff = sub.add_parser(
        "diff", help="Show differences between two resolved configs"
    )
    diff.add_argument("path_a")
    diff.add_argument("path_b")
    diff.add_argument("--defaults")

    return parser


def _json_fallback(value):
    # Flag values JSON can't represent instead of silently stringifying
    # them, so a misbehaving custom scheme handler doesn't blend in.
    return {"__unrepresentable__": type(value).__name__, "repr": repr(value)}


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    if args.command == "show":
        config = load(args.path, defaults=args.defaults, strict=args.strict)
        print(json.dumps(config, indent=2, default=_json_fallback))
    elif args.command == "resolve":
        resolve_to_file(
            args.path,
            args.output,
            defaults=args.defaults,
            strict=args.strict,
            ignore_aliases=not args.keep_aliases,
        )
        print(f"wrote resolved config to {args.output}")
    elif args.command == "diff":
        result = compare_files(
            args.path_a, args.path_b, defaults=args.defaults
        )
        for path, value in sorted(result["removed"].items()):
            print(f"- {path}: {value!r}")
        for path, value in sorted(result["added"].items()):
            print(f"+ {path}: {value!r}")
        for path, (old, new) in sorted(result["changed"].items()):
            print(f"~ {path}: {old!r} -> {new!r}")
        if not any(result.values()):
            print("no differences")

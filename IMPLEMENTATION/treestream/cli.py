from __future__ import annotations

import argparse
import sys

from . import IMPLEMENTATION_VERSION
from .errors import TreeStreamError
from .reconstructor import reconstruct
from .serializer import serialize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="treestream")
    parser.add_argument("--version", action="version", version=f"%(prog)s {IMPLEMENTATION_VERSION}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    serialize_cmd = subparsers.add_parser("serialize", help="Serialize a root directory to a TreeStream file")
    serialize_cmd.add_argument("root_directory")
    serialize_cmd.add_argument("output_file")

    reconstruct_cmd = subparsers.add_parser("reconstruct", help="Reconstruct a TreeStream file into a target directory")
    reconstruct_cmd.add_argument("serialized_file")
    reconstruct_cmd.add_argument("target_directory")
    reconstruct_cmd.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing files in target directory",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "serialize":
            serialize(args.root_directory, args.output_file)
        elif args.command == "reconstruct":
            reconstruct(args.serialized_file, args.target_directory, overwrite=args.overwrite)
        else:
            parser.error("unknown command")
    except TreeStreamError as err:
        print(str(err), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

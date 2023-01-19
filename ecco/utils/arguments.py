from argparse import ArgumentParser, Namespace
from pathlib import Path

import pkg_resources


def get_args() -> Namespace:
    """Parse and return arguments

    Returns:
        Namespace: Parsed argu
    """
    distribution = pkg_resources.get_distribution("ecco")

    parser = ArgumentParser(
        prog=distribution.project_name,
        description="An Educational C COmpiler written in Python",
    )

    parser.add_argument("PROGRAM", type=str, help="Path to input program")
    parser.add_argument("--output", "-o", type=str, help="Path to generated LLVM", default="")

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"{parser.prog} {distribution.version}",
    )

    args = parser.parse_args()
    if args.output == "":
        args.output = Path(args.PROGRAM).stem + ".ll"

    return args

from argparse import ArgumentParser, Namespace
from pathlib import Path

import pkg_resources


def get_args() -> Namespace:
    """Parse and return arguments

    Returns:
        Namespace: Parsed argu
    """
    distribution = "0.1" #pkg_resources.get_distribution("ecco")

    parser = ArgumentParser(
        prog="ecco " + distribution,
        description="An Educational C COmpiler written in Python",
    )

    parser.add_argument("PROGRAM", type=str, help="Path to input program")
    parser.add_argument(
        "--output", "-o", type=str, help="Path to generated LLVM", default=""
    )

    parser.add_argument(
        "--logging",
        "-l",
        type=str,
        help="Minimum level of log statements to print",
        choices=["NONE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help='Equivalent to --logging="NONE" (overrides --logging)',
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"{parser.prog} {distribution}",
    )

    args = parser.parse_args()

    if args.output == "":
        args.output = Path(args.PROGRAM).stem + ".ll"

    if args.quiet:
        args.logging = "NONE"

    return args

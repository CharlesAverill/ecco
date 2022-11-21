import pkg_resources
from argparse import ArgumentParser, Namespace


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

    parser.add_argument("PROGRAM", type=str, help="Filename of input program")

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"{parser.prog} {distribution.version}",
    )

    return parser.parse_args()

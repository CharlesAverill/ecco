from argparse import Namespace

from .scanning import Scanner
from .utils import get_args, setup_tracebacks

GLOBAL_SCANNER: Scanner
ARGS: Namespace


def main():
    """Entrypoint for the compiler"""
    global GLOBAL_SCANNER, ARGS, LLVM_OUT_FILE
    ARGS = get_args()

    GLOBAL_SCANNER = Scanner(ARGS.PROGRAM)
    GLOBAL_SCANNER.open()

    setup_tracebacks()
    GLOBAL_SCANNER.scan()

    # We will do some imports here to avoid "partially initialized" errors
    from .generation import generate_llvm

    generate_llvm()

    GLOBAL_SCANNER.close()


if __name__ == "__main__":
    main()

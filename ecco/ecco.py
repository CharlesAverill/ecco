from argparse import Namespace
from typing import List, TextIO

from .scanning import Scanner
from .utils import get_args, setup_tracebacks

DEBUG: bool = True
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
    from .parsing import parse_binary_expression

    parsed_ast = parse_binary_expression(0)

    generate_llvm(parsed_ast)
        
    GLOBAL_SCANNER.close()


if __name__ == "__main__":
    main()

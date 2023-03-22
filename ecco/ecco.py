from argparse import Namespace

from .scanning import Scanner
from .utils import get_args, setup_tracebacks
from .generation.symboltable import SymbolTable, SymbolTableStack

GLOBAL_SCANNER: Scanner
ARGS: Namespace
SYMBOL_TABLE_STACK: SymbolTableStack = SymbolTableStack()
GLOBAL_SYMBOL_TABLE: SymbolTable = SYMBOL_TABLE_STACK.GST


def main():
    """Entrypoint for the compiler"""
    global GLOBAL_SCANNER, ARGS, LLVM_OUT_FILE, GLOBAL_SYMBOL_TABLE
    ARGS = get_args()

    GLOBAL_SCANNER = Scanner(ARGS.PROGRAM)
    GLOBAL_SCANNER.open()

    setup_tracebacks()
    GLOBAL_SCANNER.scan()

    # We will do some imports here to avoid "partially initialized" errors
    from .generation import generate_llvm

    # SYMBOL_TABLE_STACK = SymbolTableStack()
    # GLOBAL_SYMBOL_TABLE = SYMBOL_TABLE_STACK.GST
    generate_llvm()

    GLOBAL_SCANNER.close()


if __name__ == "__main__":
    main()

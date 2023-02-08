from ..scanning import TokenType
from ..utils import EccoInternalTypeError
from ..generation.symboltable import SymbolTableEntry


def declaration_statement() -> None:
    """Parse a declaration statement

    Raises:
        EccoInternalTypeError: If an incorrect Token value is encountered
    """
    from .statement import match_token
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
    from ..generation.llvm import llvm_declare_global
    from ..generation import NumberType

    match_token(TokenType.INT)

    ident = match_token(TokenType.IDENTIFIER)

    if type(ident) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/declaration.py:declaration_statement",
        )

    GLOBAL_SYMBOL_TABLE.update(ident, SymbolTableEntry(ident, 0, NumberType.INT))

    llvm_declare_global(ident, 0)

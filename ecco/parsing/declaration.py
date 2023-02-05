from .ecco_ast import ASTNode
from .statement import match_token
from ..scanning import TokenType
from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
from ..utils import EccoInternalTypeError


def declaration_statement() -> None:
    match_token(TokenType.INT)

    match_token(TokenType.IDENTIFIER)

    ident = GLOBAL_SCANNER.current_token.value
    if type(GLOBAL_SCANNER.current_token.value) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/declaration.py:declaration_statement",
        )

    GLOBAL_SYMBOL_TABLE.update(ident, 0)

    # llvm_generate_global_variable

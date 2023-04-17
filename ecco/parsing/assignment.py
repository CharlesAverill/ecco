from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from ..utils import EccoInternalTypeError, EccoFatalException
from typing import Optional


def assignment_statement() -> ASTNode:
    """Parse an assignment statement

    Raises:
        EccoInternalTypeError: If an incorrect identifier type is encountered
        EccoFatalException: If an undefined variable is encountered

    Returns:
        ASTNode: ASTNode encoding assignment tree
    """
    from .statement import match_token
    from .expression import parse_binary_expression
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK
    from ..generation import SymbolTableEntry

    left: ASTNode
    right: ASTNode
    tree: ASTNode

    ident = match_token(TokenType.IDENTIFIER)[0]
    if not isinstance(ident, str):
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/assignment.py:assignment_statement",
        )

    symbol: Optional[SymbolTableEntry] = SYMBOL_TABLE_STACK[ident]
    if symbol is None:
        raise EccoFatalException("", f'Undefined variable "{ident}"')
    # elif isinstance(symbol.identifier_type.contents, Function):
    #     return function_call_expression(symbol.identifier_name)

    right = ASTNode(Token(TokenType.IDENTIFIER, ident), None, None, None)

    match_token(TokenType.ASSIGN)

    left = parse_binary_expression()

    tree = ASTNode(Token(TokenType.ASSIGN), left, None, right)

    return tree

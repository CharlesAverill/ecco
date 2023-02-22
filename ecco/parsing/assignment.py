from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from ..utils import EccoInternalTypeError, EccoFatalException
from ..generation.types import Function
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
    from .expression import parse_binary_expression, function_call_expression
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
    from ..generation import SymbolTableEntry

    left: ASTNode
    right: ASTNode
    tree: ASTNode

    ident = match_token(TokenType.IDENTIFIER)[0]
    if type(ident) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/assignment.py:assignment_statement",
        )

    symbol: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[ident]
    if symbol is None:
        raise EccoFatalException("", f'Undefined variable "{ident}"')
    elif type(symbol.identifier_type.contents) == Function:
        return function_call_expression(symbol.identifier_name)

    right = ASTNode(Token(TokenType.LEFTVALUE_IDENTIFIER, ident), None, None, None)

    match_token(TokenType.ASSIGN)

    left = parse_binary_expression(0)

    tree = ASTNode(Token(TokenType.ASSIGN), left, None, right)

    return tree

from .ecco_ast import ASTNode
from .statement import match_token
from ..scanning import TokenType, Token
from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
from ..utils import EccoInternalTypeError, EccoFatalException
from .expression import parse_binary_expression

def assignment_statement() -> ASTNode:
    left: ASTNode
    right: ASTNode
    tree: ASTNode

    match_token(TokenType.IDENTIFIER)
    if type(GLOBAL_SCANNER.current_token.value) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/assignment.py:assignment_statement",
        )
    ident = GLOBAL_SCANNER.current_token.value

    if GLOBAL_SYMBOL_TABLE[ident] is None:
        raise EccoFatalException("", f"Undefined variable \"{ident}\"")

    right = ASTNode(Token(TokenType.LEFTVALUE_IDENTIFIER, ident), None, None)

    match_token(TokenType.ASSIGN)

    left = parse_binary_expression(0)

    tree = ASTNode(Token(TokenType.ASSIGN), left, right)
    
    return tree

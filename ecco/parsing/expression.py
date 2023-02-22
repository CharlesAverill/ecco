from typing import Dict

from ..scanning import Token, TokenType
from ..utils import (
    EccoSyntaxError,
    EccoEOFMissingSemicolonError,
    EccoIdentifierError,
    EccoInternalTypeError,
)
from .ecco_ast import ASTNode
from typing import Optional
from ..generation.symboltable import SymbolTableEntry
from .statement import match_token

from ..generation.types import Function

OPERATOR_PRECEDENCE: Dict[TokenType, int] = {
    TokenType.PLUS: 12,
    TokenType.MINUS: 12,
    TokenType.STAR: 13,
    TokenType.SLASH: 13,
    TokenType.EQ: 10,
    TokenType.NEQ: 10,
    TokenType.LT: 11,
    TokenType.LEQ: 11,
    TokenType.GT: 11,
    TokenType.GEQ: 11,
}


def parse_terminal_node() -> ASTNode:
    """Process GLOBAL_SCANNER.current_token into an ASTNode

    Raises:
        EccoSyntaxError: If a non-terminal token is detected

    Returns:
        ASTNode: An ASTNode storing the parsed terminal token information
    """
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE

    out: ASTNode
    if GLOBAL_SCANNER.current_token.type == TokenType.INTEGER_LITERAL:
        out = ASTNode(GLOBAL_SCANNER.current_token, None, None, None)
    elif GLOBAL_SCANNER.current_token.type == TokenType.IDENTIFIER:
        ident: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[
            str(GLOBAL_SCANNER.current_token.value)
        ]
        if not ident:
            raise EccoIdentifierError(
                f'Undeclared variable "{GLOBAL_SCANNER.current_token.value}"'
            )

        if type(ident.identifier_type.contents) == Function:
            match_token(TokenType.IDENTIFIER)
            return function_call_expression(ident.identifier_name)
        else:
            out = ASTNode(
                Token(TokenType.IDENTIFIER, ident.identifier_name), None, None, None
            )
    elif GLOBAL_SCANNER.current_token.type == TokenType.EOF:
        raise EccoEOFMissingSemicolonError()
    else:
        raise EccoSyntaxError(
            f'Expected terminal Token but got "{str(GLOBAL_SCANNER.current_token.type)}"'
        )

    GLOBAL_SCANNER.scan()
    return out


def function_call_expression(function_name_override: str = "") -> ASTNode:
    from ..ecco import GLOBAL_SYMBOL_TABLE, GLOBAL_SCANNER

    # By the time we're executing code on the inside of function_call_expression,
    # we've already scanned in an identifier
    if type(GLOBAL_SCANNER.current_token.value) != str:
        if not function_name_override:
            raise EccoInternalTypeError(
                "str",
                str(type(GLOBAL_SCANNER.current_token.value)),
                "expression.py:function_call_expression",
            )
    elif not function_name_override:
        function_name_override = GLOBAL_SCANNER.current_token.value

    ident: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name_override]
    if not ident:
        raise EccoIdentifierError(
            f'Tried to call undeclared function "{function_name_override}"'
        )
    elif type(ident.identifier_type.contents) != Function:
        raise EccoIdentifierError(
            "Tried to call function with identifier bound to number value"
        )

    match_token(TokenType.LEFT_PARENTHESIS)

    # Functions will take one argument for now
    single_argument: ASTNode = parse_binary_expression(0)

    match_token(TokenType.RIGHT_PARENTHESIS)

    out: ASTNode = ASTNode(
        Token(TokenType.FUNCTION_CALL, ident.identifier_name), single_argument
    )

    return out


def error_check_precedence(node_type: TokenType) -> int:
    """Checks an operator's precedence, with error checking

    Args:
        node_type (TokenType): Type of operator to get precedence of

    Raises:
        EccoSyntaxError: If node_type is a non-operator type

    Returns:
        int: The precedence of the passed operator Token
    """
    if node_type not in OPERATOR_PRECEDENCE:
        raise EccoSyntaxError(f"Expected operator but got {node_type}")

    return OPERATOR_PRECEDENCE[node_type]


def parse_binary_expression(previous_token_precedence: int) -> ASTNode:
    """Perform Pratt parsing on a binary expression

    Args:
        previous_token_precedence (int): The precedence of the last-encountered
                                         token, or 0 if no operators have been
                                         encountered yet

    Returns:
        ASTNode: An ASTNode encoding the entire binary expression
    """
    from ..ecco import GLOBAL_SCANNER

    left: ASTNode
    right: ASTNode
    node_type: TokenType

    # Get an integer literal, and scan the next token into
    # GLOBAL_SCANNER.current_token
    left = parse_terminal_node()

    # Reached the end of a statement
    node_type = GLOBAL_SCANNER.current_token.type
    if node_type in [TokenType.SEMICOLON, TokenType.RIGHT_PARENTHESIS]:
        return left
    elif node_type == TokenType.EOF:
        raise EccoEOFMissingSemicolonError()

    # As long as the precedence of the current token is less than the precedence
    # of the previous token
    while error_check_precedence(node_type) > previous_token_precedence:
        # Scan the next Token
        GLOBAL_SCANNER.scan()

        # Recursively build the right AST subtree
        right = parse_binary_expression(OPERATOR_PRECEDENCE[node_type])

        # Join right subtree with current left subtree
        left = ASTNode(Token(node_type), left, None, right)

        # Update node_type and check for end of statement
        node_type = GLOBAL_SCANNER.current_token.type
        if node_type in [TokenType.SEMICOLON, TokenType.RIGHT_PARENTHESIS]:
            break
        elif node_type == TokenType.EOF:
            raise EccoEOFMissingSemicolonError()

    return left

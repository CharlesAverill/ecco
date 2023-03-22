from typing import Dict, List

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
from .optimization import optimize_AST

from ..generation.types import Function

OPERATOR_PRECEDENCE: Dict[TokenType, int] = {
    TokenType.PLUS: 12,
    TokenType.MINUS: 12,
    TokenType.STAR: 13,
    TokenType.SLASH: 13,
    TokenType.EQ: 9,
    TokenType.NEQ: 9,
    TokenType.LT: 10,
    TokenType.LEQ: 10,
    TokenType.GT: 10,
    TokenType.GEQ: 10,
    TokenType.ASSIGN: 1,
}

RIGHT_ASSOCIATIVITY_OPERATORS: List[TokenType] = [TokenType.ASSIGN]


def parse_terminal_node() -> ASTNode:
    """Process GLOBAL_SCANNER.current_token into an ASTNode

    Raises:
        EccoSyntaxError: If a non-terminal token is detected

    Returns:
        ASTNode: An ASTNode storing the parsed terminal token information
    """
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK

    out: ASTNode
    if GLOBAL_SCANNER.current_token.type == TokenType.INTEGER_LITERAL:
        out = ASTNode(GLOBAL_SCANNER.current_token, None, None, None)
    elif GLOBAL_SCANNER.current_token.type == TokenType.IDENTIFIER:
        ident: Optional[SymbolTableEntry] = SYMBOL_TABLE_STACK[
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


def prefix_operator_passthrough() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER

    out: ASTNode

    if GLOBAL_SCANNER.current_token.type == TokenType.AMPERSAND:
        GLOBAL_SCANNER.scan()
        out = prefix_operator_passthrough()

        if out.type != TokenType.IDENTIFIER:
            raise EccoSyntaxError(
                "Address operators must be succeeded by variable names"
            )

        out.token.type = TokenType.AMPERSAND

        out.tree_type.pointer_depth += 1
    elif GLOBAL_SCANNER.current_token.type == TokenType.STAR:
        GLOBAL_SCANNER.scan()
        out = prefix_operator_passthrough()

        if out.type not in [TokenType.IDENTIFIER, TokenType.DEREFERENCE]:
            raise EccoSyntaxError(
                "Dereference operators must be succeeded by dereference operators or variable names"
            )

        out.tree_type.pointer_depth -= 1
        out = ASTNode(Token(TokenType.DEREFERENCE), out)

        if out.left:
            out.token.value = out.left.token.value
    else:
        out = parse_terminal_node()

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

    expected_args = ident.identifier_type.contents.arguments

    match_token(TokenType.LEFT_PARENTHESIS)

    passed_args: List[ASTNode] = []
    for arg_index in range(len(expected_args)):
        if arg_index > 0:
            match_token(TokenType.COMMA)
        # We won't do type checking here yet
        passed_args.append(parse_binary_expression())

    match_token(TokenType.RIGHT_PARENTHESIS)

    out: ASTNode = ASTNode(
        Token(TokenType.FUNCTION_CALL, ident.identifier_name),
        function_call_arguments=passed_args,
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


def _parse_binary_expression_recursive(previous_token_precedence: int) -> ASTNode:
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

    # Get an integer literal, variable instance, or function call, and scan the
    # next token into GLOBAL_SCANNER.current_token
    left = prefix_operator_passthrough()  # parse_terminal_node()

    # Reached the end of a statement
    node_type = GLOBAL_SCANNER.current_token.type
    if node_type in [TokenType.SEMICOLON, TokenType.RIGHT_PARENTHESIS, TokenType.COMMA]:
        left.is_rvalue = True
        return left
    elif node_type == TokenType.EOF:
        raise EccoEOFMissingSemicolonError()

    # As long as the precedence of the current token is less than the precedence
    # of the previous token
    while (error_check_precedence(node_type) > previous_token_precedence) or (
        error_check_precedence(node_type) == previous_token_precedence
        and node_type in RIGHT_ASSOCIATIVITY_OPERATORS
    ):
        # Scan the next Token
        GLOBAL_SCANNER.scan()

        # Recursively build the right AST subtree
        right = _parse_binary_expression_recursive(OPERATOR_PRECEDENCE[node_type])

        if node_type == TokenType.ASSIGN:
            # When assigning, we want to swap the left and right children
            # so that right-associativity is maintained
            # We also want assignment statements to be rvalues, so that we
            # can perform array accesses and multiple assignments
            right.is_rvalue = True
            left, right = right, left
        else:
            left.is_rvalue = right.is_rvalue = True

        # Join right subtree with current left subtree
        left = ASTNode(Token(node_type), left, None, right)

        # Update node_type and check for end of statement
        node_type = GLOBAL_SCANNER.current_token.type
        if node_type in [
            TokenType.SEMICOLON,
            TokenType.RIGHT_PARENTHESIS,
            TokenType.COMMA,
        ]:
            break
        elif node_type == TokenType.EOF:
            raise EccoEOFMissingSemicolonError()

    left.is_rvalue = True
    return left


def parse_binary_expression() -> ASTNode:
    """Wrapper function for parsing binary expressions

    Returns:
        ASTNode: Expression AST
    """
    root = optimize_AST(_parse_binary_expression_recursive(0))

    return root

from ..scanning import Token, TokenType
from ..utils import EccoSyntaxError
from .ecco_ast import ASTNode, create_ast_leaf
from ..ecco import GLOBAL_SCANNER


OPERATOR_PRECEDENCE: dict[TokenType, int] = {
    TokenType.PLUS: 12,
    TokenType.MINUS: 12,
    TokenType.STAR: 13,
    TokenType.SLASH: 13,
}


def parse_terminal_node() -> ASTNode:
    """Process GLOBAL_SCANNER.current_token into an ASTNode

    Raises:
        EccoSyntaxError: If a non-terminal token is detected

    Returns:
        ASTNode: An ASTNode storing the parsed terminal token information
    """
    out: ASTNode
    if GLOBAL_SCANNER.current_token.type == TokenType.INTEGER_LITERAL:
        out = create_ast_leaf(GLOBAL_SCANNER.current_token)
        GLOBAL_SCANNER.scan()
        return out
    else:
        raise EccoSyntaxError(
            f'Expected terminal Token but got "{str(GLOBAL_SCANNER.current_token.type)}"'
        )


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
    left: ASTNode
    right: ASTNode
    node_type: TokenType

    # Get an integer literal, and scan the next token into
    # GLOBAL_SCANNER.current_token
    left = parse_terminal_node()

    # Reached EOF
    node_type = GLOBAL_SCANNER.current_token.type
    if GLOBAL_SCANNER.current_token.type == TokenType.EOF:
        return left

    # As long as the precedence of the current token is less than the precedence
    # of the previous token
    while error_check_precedence(node_type) > previous_token_precedence:
        # Scan the next Token
        GLOBAL_SCANNER.scan()

        # Recursively build the right AST subtree
        right = parse_binary_expression(OPERATOR_PRECEDENCE[node_type])

        # Join right subtree with current left subtree
        left = ASTNode(Token(node_type), left, right)

        # Update node_type and check for EOF
        node_type = GLOBAL_SCANNER.current_token.type
        if node_type == TokenType.EOF:
            return left

    return left

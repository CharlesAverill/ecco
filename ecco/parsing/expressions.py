from ..scanning import Token, TokenType
from ..utils import EccoSyntaxError
from ..ecco_ast import ASTNode, create_ast_leaf
from ..ecco import GLOBAL_SCANNER


def parse_terminal_node() -> ASTNode:
    out: ASTNode
    if GLOBAL_SCANNER.current_token.type == TokenType.INTEGER_LITERAL:
        out = create_ast_leaf(GLOBAL_SCANNER.current_token)
        GLOBAL_SCANNER.scan()
        return out
    else:
        raise EccoSyntaxError(
            f'Expected terminal Token but got "{str(GLOBAL_SCANNER.current_token.type)}"'
        )


def parse_binary_expression() -> ASTNode:
    left: ASTNode
    right: ASTNode
    node_type: TokenType

    # Get an integer literal, and scan the next token into GLOBAL_SCANNER.current_token
    left = parse_terminal_node()

    # Reached EOF
    if GLOBAL_SCANNER.current_token.type == TokenType.EOF:
        return left

    # If we haven't reached EOF, we're looking at an operator (hopefully)
    # We want to store this value so we can make an AST operator node
    # with integer literals (or sub-expressions) as children
    node_type = GLOBAL_SCANNER.current_token.type

    # Scan the next token
    GLOBAL_SCANNER.scan()

    # Recursively parse the expression to the right of
    right = parse_binary_expression()

    return ASTNode(Token(node_type), left, right)

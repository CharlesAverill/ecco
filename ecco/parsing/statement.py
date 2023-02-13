from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from .expression import parse_binary_expression
from ..utils import EccoSyntaxError, EccoFatalException
from typing import Generator, Optional, Union
from .declaration import declaration_statement
from .assignment import assignment_statement


def match_token(tt: TokenType) -> Union[str, int]:
    """Ensure the current token is of a certain type, then scan another token

    Args:
        tt (TokenType): TokenType to match

    Raises:
        EccoSyntaxError: If an incorrect token type is encountered

    Returns:
        Union[str, int]: The value of the matching token
    """
    from ..ecco import GLOBAL_SCANNER

    if GLOBAL_SCANNER.current_token.type == tt:
        token_value = GLOBAL_SCANNER.current_token.value
        GLOBAL_SCANNER.scan()
        return token_value

    raise EccoSyntaxError(
        f'Expected "{str(tt)}" but got "{str(GLOBAL_SCANNER.current_token.type)}"'
    )


def print_statement() -> ASTNode:
    match_token(TokenType.PRINT)

    tree = parse_binary_expression(0)

    tree = ASTNode(Token(TokenType.PRINT), tree, None, None)

    return tree


def if_statement() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER

    # Match some syntax
    match_token(TokenType.IF)
    match_token(TokenType.LEFT_PARENTHESIS)

    # Get the condition tree
    condition_tree: ASTNode = parse_binary_expression(0)
    if not condition_tree.token.is_comparison_operator():
        raise EccoFatalException(
            f"Branch statements currently require a conditional operand, not {condition_tree.token}"
        )

    match_token(TokenType.RIGHT_PARENTHESIS)

    # Now we need to parse the code that will execute if the IF operand evaluates to 1
    conditional_block: ASTNode = next(parse_statements())

    conditional_converse_block: Optional[ASTNode] = None

    if GLOBAL_SCANNER.current_token.type == TokenType.ELSE:
        match_token(TokenType.ELSE)
        conditional_converse_block = next(parse_statements())

    return ASTNode(
        Token(TokenType.IF),
        condition_tree,
        conditional_block,
        conditional_converse_block,
    )


def parse_statements() -> Generator[ASTNode, None, None]:
    from ..ecco import GLOBAL_SCANNER

    root: ASTNode = ASTNode(Token(TokenType.UNKNOWN_TOKEN))
    left: Optional[ASTNode] = None

    match_token(TokenType.LEFT_BRACE)

    while True:
        match_semicolon: bool = True
        return_left: bool = False

        if GLOBAL_SCANNER.current_token.type == TokenType.PRINT:
            root = print_statement()
        elif GLOBAL_SCANNER.current_token.type == TokenType.INT:
            declaration_statement()
            root.token.type = TokenType.UNKNOWN_TOKEN
        elif GLOBAL_SCANNER.current_token.type == TokenType.IDENTIFIER:
            root = assignment_statement()
        elif GLOBAL_SCANNER.current_token.type == TokenType.IF:
            root = if_statement()
            match_semicolon = False
        elif GLOBAL_SCANNER.current_token.type == TokenType.RIGHT_BRACE:
            match_token(TokenType.RIGHT_BRACE)
            match_semicolon = False
            return_left = True
        else:
            raise EccoSyntaxError(
                f'Unexpected token "{str(GLOBAL_SCANNER.current_token.type)}"'
            )

        if return_left:
            if left:
                yield left
            break

        if match_semicolon:
            match_token(TokenType.SEMICOLON)

        if root.type != TokenType.UNKNOWN_TOKEN:
            if not left:
                left = root
            else:
                left = ASTNode(Token(TokenType.AST_GLUE), left, None, root)
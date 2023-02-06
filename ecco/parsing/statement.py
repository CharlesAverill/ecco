from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from .expression import parse_binary_expression
from ..utils import EccoSyntaxError
from typing import Generator, Optional, Union
from .declaration import declaration_statement
from .assignment import assignment_statement


def match_token(tt: TokenType) -> Union[str, int]:
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

    tree = ASTNode(Token(TokenType.PRINT), tree, None)

    return tree


def parse_statements() -> Generator[ASTNode, None, None]:
    from ..ecco import GLOBAL_SCANNER

    tree: Optional[ASTNode] = None
    match_semicolon: bool = True

    while GLOBAL_SCANNER.current_token.type != TokenType.EOF:
        if GLOBAL_SCANNER.current_token.type == TokenType.PRINT:
            tree = print_statement()
        elif GLOBAL_SCANNER.current_token.type == TokenType.INT:
            declaration_statement()
        elif GLOBAL_SCANNER.current_token.type == TokenType.IDENTIFIER:
            tree = assignment_statement()
        else:
            raise EccoSyntaxError(
                'Unexpected token "{str(GLOBAL_SCANNER.current_token.type)}"'
            )

        if match_semicolon:
            match_token(TokenType.SEMICOLON)

        if tree:
            yield tree

        tree = None

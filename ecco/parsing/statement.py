from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from ..utils import EccoSyntaxError, EccoFatalException
from typing import Optional, Union, List, Tuple
from .declaration import declaration_statement
from .assignment import assignment_statement
from ..generation.symboltable import SymbolTableEntry
from ..generation.types import Number, NumberType, Function


def match_token(
    tt: Union[TokenType, List[TokenType]]
) -> Tuple[Union[str, int], TokenType]:
    """Ensure the current token is of a certain type, then scan another token

    Args:
        tt (TokenType): TokenType to match

    Raises:
        EccoSyntaxError: If an incorrect token type is encountered

    Returns:
        Union[str, int]: The value of the matching token
    """
    from ..ecco import GLOBAL_SCANNER

    if (type(tt) == TokenType and GLOBAL_SCANNER.current_token.type == tt) or (
        type(tt) == list and GLOBAL_SCANNER.current_token.type in tt
    ):
        token_value = GLOBAL_SCANNER.current_token.value
        token_type = GLOBAL_SCANNER.current_token.type
        GLOBAL_SCANNER.scan()
        return (token_value, token_type)

    raise EccoSyntaxError(
        f'Expected "{str(tt)}" but got "{str(GLOBAL_SCANNER.current_token.type)}"'
    )


def match_type() -> Number:
    """Match a type token

    Returns:
        Number: Number containing data type and pointer depth
    """
    from ..ecco import GLOBAL_SCANNER

    ttype = match_token([TokenType.INT, TokenType.CHAR])[1]

    pointer_depth = 0
    while GLOBAL_SCANNER.current_token.type == TokenType.STAR:
        match_token(TokenType.STAR)
        pointer_depth += 1

    return Number(NumberType.from_tokentype(ttype), 0, pointer_depth)


def print_statement() -> ASTNode:
    from .expression import parse_binary_expression

    match_token(TokenType.PRINT)

    tree = parse_binary_expression(0)

    tree = ASTNode(Token(TokenType.PRINT), tree, None, None)

    return tree


def if_statement() -> ASTNode:
    from .expression import parse_binary_expression
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
    conditional_block: ASTNode = parse_statements()

    conditional_converse_block: Optional[ASTNode] = None

    if GLOBAL_SCANNER.current_token.type == TokenType.ELSE:
        match_token(TokenType.ELSE)
        conditional_converse_block = parse_statements()

    return ASTNode(
        Token(TokenType.IF),
        condition_tree,
        conditional_block,
        conditional_converse_block,
    )


def while_statement() -> ASTNode:
    from .expression import parse_binary_expression

    # Match some syntax
    match_token(TokenType.WHILE)
    match_token(TokenType.LEFT_PARENTHESIS)

    # Get the condition tree
    condition_tree: ASTNode = parse_binary_expression(0)
    if not condition_tree.token.is_comparison_operator():
        raise EccoFatalException(
            f"Branch statements currently require a conditional operand, not {condition_tree.token}"
        )

    match_token(TokenType.RIGHT_PARENTHESIS)

    # Now we need to parse the code that will execute if the IF operand evaluates to 1
    conditional_block: ASTNode = parse_statements()

    return ASTNode(Token(TokenType.WHILE), condition_tree, None, conditional_block)


def for_statement() -> ASTNode:
    from .expression import parse_binary_expression

    match_token(TokenType.FOR)
    match_token(TokenType.LEFT_PARENTHESIS)

    for_preamble: ASTNode = assignment_statement()
    match_token(TokenType.SEMICOLON)

    # Get the condition tree
    condition_tree: ASTNode = parse_binary_expression(0)
    if not condition_tree.token.is_comparison_operator():
        raise EccoFatalException(
            f"Branch statements currently require a conditional operand, not {condition_tree.token}"
        )
    match_token(TokenType.SEMICOLON)

    for_postamble: ASTNode = assignment_statement()
    match_token(TokenType.RIGHT_PARENTHESIS)

    conditional_block: ASTNode = parse_statements()

    out: ASTNode = ASTNode(
        Token(TokenType.AST_GLUE), conditional_block, None, for_postamble
    )
    out = ASTNode(Token(TokenType.WHILE), condition_tree, None, out)
    out = ASTNode(Token(TokenType.AST_GLUE), for_preamble, None, out)

    return out


def return_statement() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
    from .expression import parse_binary_expression

    match_token(TokenType.RETURN)

    ident: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[
        GLOBAL_SCANNER.current_function_name
    ]
    if not ident:
        raise EccoFatalException("", "Lost track of current function!")

    if ident.identifier_type.ttype == TokenType.VOID:
        return ASTNode(Token(TokenType.RETURN, GLOBAL_SCANNER.current_function_name))

    return ASTNode(
        Token(TokenType.RETURN, GLOBAL_SCANNER.current_function_name),
        parse_binary_expression(0),
    )


def parse_statements() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE

    root: ASTNode = ASTNode(Token(TokenType.UNKNOWN_TOKEN))
    left: Optional[ASTNode] = None

    match_token(TokenType.LEFT_BRACE)

    while True:
        match_semicolon: bool = True
        return_left: bool = False

        if GLOBAL_SCANNER.current_token.type == TokenType.PRINT:
            root = print_statement()
        elif GLOBAL_SCANNER.current_token.type.is_type():
            declaration_statement()
            root = ASTNode(Token(TokenType.UNKNOWN_TOKEN))
        elif GLOBAL_SCANNER.current_token.type == TokenType.IDENTIFIER:
            gse = GLOBAL_SYMBOL_TABLE[str(GLOBAL_SCANNER.current_token.value)]
            if gse and type(gse.identifier_type.contents) == Number:
                root = assignment_statement()
            elif gse and type(gse.identifier_type.contents) == Function:
                from .expression import function_call_expression

                ident = str(GLOBAL_SCANNER.current_token.value)
                match_token(TokenType.IDENTIFIER)
                root = function_call_expression(ident)
        elif GLOBAL_SCANNER.current_token.type == TokenType.IF:
            root = if_statement()
            match_semicolon = False
        elif GLOBAL_SCANNER.current_token.type == TokenType.WHILE:
            root = while_statement()
            match_semicolon = False
        elif GLOBAL_SCANNER.current_token.type == TokenType.FOR:
            root = for_statement()
            match_semicolon = False
        elif GLOBAL_SCANNER.current_token.type == TokenType.RIGHT_BRACE:
            match_token(TokenType.RIGHT_BRACE)
            match_semicolon = False
            return_left = True
        elif GLOBAL_SCANNER.current_token.type == TokenType.RETURN:
            root = return_statement()
        else:
            raise EccoSyntaxError(
                f'Unexpected token "{str(GLOBAL_SCANNER.current_token.type)}"'
            )

        if return_left:
            if left:
                return left
            else:
                return root

        if match_semicolon:
            match_token(TokenType.SEMICOLON)

        if root.type != TokenType.UNKNOWN_TOKEN:
            if not left:
                left = root
            else:
                left = ASTNode(Token(TokenType.AST_GLUE), left, None, root)

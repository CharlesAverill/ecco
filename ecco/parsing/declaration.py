from ..scanning import TokenType, Token
from ..utils import EccoInternalTypeError, EccoIdentifierError
from ..generation.symboltable import SymbolTableEntry
from ..generation.types import Type, Function, Number, NumberType
from .ecco_ast import ASTNode
from typing import Union


def function_declaration_statement() -> ASTNode:
    """Parse a function declaration statement

    Returns:
        ASTNode: AST containing entire program within function
    """
    from .statement import match_token, parse_statements
    from ..ecco import GLOBAL_SYMBOL_TABLE

    match_token(TokenType.VOID)
    identifier: Union[str, int] = match_token(TokenType.IDENTIFIER)[0]
    if type(identifier) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(identifier)),
            "declaration.py:function_declaration_statement",
        )
    elif GLOBAL_SYMBOL_TABLE[identifier]:
        raise EccoIdentifierError(
            f'Function with name "{identifier}" already defined in this scope'
        )
    GLOBAL_SYMBOL_TABLE[identifier] = SymbolTableEntry(
        identifier, Type(TokenType.FUNCTION, Function(TokenType.VOID))
    )

    match_token(TokenType.LEFT_PARENTHESIS)
    match_token(TokenType.RIGHT_PARENTHESIS)

    return ASTNode(
        Token(TokenType.FUNCTION, identifier), parse_statements(), None, None
    )


def declaration_statement() -> None:
    """Parse a declaration statement

    Raises:
        EccoInternalTypeError: If an incorrect Token value is encountered
    """
    from .statement import match_token
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
    from ..generation.llvm import llvm_declare_global

    ttype = match_token([TokenType.INT, TokenType.CHAR])[1]

    ident = match_token(TokenType.IDENTIFIER)[0]

    if type(ident) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/declaration.py:declaration_statement",
        )

    GLOBAL_SYMBOL_TABLE.update(
        ident,
        SymbolTableEntry(
            ident, Type(ttype, Number(NumberType.from_tokentype(ttype), 0))
        ),
    )

    ste = GLOBAL_SYMBOL_TABLE[ident]
    if ste and type(ste.identifier_type.contents) == Number:
        llvm_declare_global(ident, 0, ste.identifier_type.contents.ntype)
    else:
        raise EccoIdentifierError("Failed to insert identifier into GST")

from ..scanning import TokenType, Token
from ..utils import EccoInternalTypeError, EccoIdentifierError
from ..generation.symboltable import SymbolTableEntry
from ..generation.types import Type, Function, Number
from .ecco_ast import ASTNode
from typing import Union, Dict


def function_declaration_statement() -> ASTNode:
    """Parse a function declaration statement

    Returns:
        ASTNode: AST containing entire program within function
    """
    from .statement import match_token, parse_statements, match_type
    from ..ecco import GLOBAL_SYMBOL_TABLE, GLOBAL_SCANNER, SYMBOL_TABLE_STACK
    from ..generation.llvmvalue import LLVMValue, LLVMValueType

    return_type: Number = match_type()
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

    match_token(TokenType.LEFT_PARENTHESIS)

    # Grab arguments
    arguments: Dict[str, Number] = {}
    while GLOBAL_SCANNER.current_token.type != TokenType.RIGHT_PARENTHESIS:
        if len(arguments) and GLOBAL_SCANNER.current_token.type == TokenType.COMMA:
            match_token(TokenType.COMMA)

        arg_type: Number = match_type()
        arg_name: str = str(match_token(TokenType.IDENTIFIER)[0])

        arguments.update({arg_name: arg_type})

        SYMBOL_TABLE_STACK.LST[arg_name] = SymbolTableEntry(
            arg_name,
            Type(arg_type.ntype.to_tokentype(), arg_type),
            LLVMValue(
                LLVMValueType.VIRTUAL_REGISTER,
                arg_name,
                arg_type.ntype,
                arg_type.pointer_depth,
            ),
        )

    match_token(TokenType.RIGHT_PARENTHESIS)

    GLOBAL_SCANNER.current_function_name = identifier
    GLOBAL_SYMBOL_TABLE[identifier] = SymbolTableEntry(
        identifier, Type(TokenType.FUNCTION, Function(return_type, arguments))
    )

    return ASTNode(
        Token(TokenType.FUNCTION, identifier), parse_statements(), None, None
    )


def declaration_statement() -> None:
    """Parse a declaration statement

    Raises:
        EccoInternalTypeError: If an incorrect Token value is encountered
    """
    from .statement import match_token, match_type
    from ..ecco import GLOBAL_SCANNER, GLOBAL_SYMBOL_TABLE
    from ..generation.llvm import llvm_declare_global

    num = match_type()

    ident = match_token(TokenType.IDENTIFIER)[0]

    if type(ident) != str:
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/declaration.py:declaration_statement",
        )

    num.pointer_depth += 1
    GLOBAL_SYMBOL_TABLE[ident] = SymbolTableEntry(
        ident, Type(num.ntype.to_tokentype(), num)
    )

    ste = GLOBAL_SYMBOL_TABLE[ident]
    if ste and type(ste.identifier_type.contents) == Number:
        llvm_declare_global(ident, 0, num)
    else:
        raise EccoIdentifierError("Failed to insert identifier into GST")

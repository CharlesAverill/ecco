from ..scanning import TokenType, Token
from ..utils import EccoInternalTypeError, EccoIdentifierError, EccoArrayError
from ..generation.symboltable import SymbolTableEntry
from ..generation.types import Type, Function, Number, Array, Struct
from .ecco_ast import ASTNode
from typing import Union, Optional, List
from collections import OrderedDict


def function_declaration_statement() -> ASTNode:
    """Parse a function declaration statement

    Returns:
        ASTNode: AST containing entire program within function
    """
    from .statement import match_token, parse_statements, match_type
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK
    from ..generation.llvmvalue import LLVMValue, LLVMValueType

    return_type: Number = match_type()
    identifier: Union[str, int] = match_token(TokenType.IDENTIFIER)[0]
    if not isinstance(identifier, str):
        raise EccoInternalTypeError(
            "str",
            str(type(identifier)),
            "declaration.py:function_declaration_statement",
        )

    gst_entry: Optional[SymbolTableEntry] = SYMBOL_TABLE_STACK.GST[identifier]
    expecting_definition: bool = False
    if gst_entry:
        if not isinstance(gst_entry.identifier_type.contents, Function):
            raise EccoIdentifierError(
                f'Function with name "{identifier}" already defined in this scope'
            )
        expecting_definition = gst_entry.identifier_type.contents.is_prototype

    if expecting_definition and (
        gst_entry
        and isinstance(gst_entry.identifier_type.contents, Function)
        and return_type != gst_entry.identifier_type.contents.return_type
    ):
        raise EccoIdentifierError(
            f'Function "{identifier}" expected to have return type {gst_entry.identifier_type.contents.return_type} but got {return_type}'
        )

    match_token(TokenType.LEFT_PARENTHESIS)

    # Grab arguments
    arguments: OrderedDict[str, Number] = OrderedDict()
    expected_arguments: Optional[List[Number]] = None
    if (
        expecting_definition
        and gst_entry
        and isinstance(gst_entry.identifier_type.contents, Function)
    ):
        expected_arguments = list(gst_entry.identifier_type.contents.arguments.values())

    while GLOBAL_SCANNER.current_token.type != TokenType.RIGHT_PARENTHESIS:
        if len(arguments) and GLOBAL_SCANNER.current_token.type == TokenType.COMMA:
            match_token(TokenType.COMMA)

        arg_type: Number = match_type()
        arg_name: str = str(match_token(TokenType.IDENTIFIER)[0])

        if (
            expecting_definition
            and expected_arguments
            and expected_arguments[len(arguments)] != arg_type
        ):
            raise EccoIdentifierError(
                f'Function argument "{arg_name}" was expected to have type {expected_arguments[len(arguments)]}, but got {arg_type}'
            )

        arguments[arg_name] = arg_type

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
    if expected_arguments and len(arguments) != len(expected_arguments):
        raise EccoIdentifierError(
            f'Function "{identifier}" expected to have {len(expected_arguments)} arguments, but got {len(arguments)}'
        )

    match_token(TokenType.RIGHT_PARENTHESIS)

    GLOBAL_SCANNER.current_function_name = identifier
    if (
        expecting_definition
        and gst_entry
        and isinstance(gst_entry.identifier_type.contents, Function)
    ):
        gst_entry.identifier_type.contents.arguments = arguments
    else:
        gst_entry = SYMBOL_TABLE_STACK.GST[identifier] = SymbolTableEntry(
            identifier, Type(TokenType.FUNCTION, Function(return_type, arguments))
        )

    # Just parsed a function prototype
    if GLOBAL_SCANNER.current_token.type == TokenType.SEMICOLON:
        if gst_entry and isinstance(gst_entry.identifier_type.contents, Function):
            gst_entry.identifier_type.contents.is_prototype = True
        if expecting_definition:
            raise EccoIdentifierError(
                f'Function prototype with name "{identifier}" has already been declared, expected definition'
            )

        match_token(TokenType.SEMICOLON)
        return ASTNode(Token(TokenType.UNKNOWN_TOKEN))

    return ASTNode(
        Token(TokenType.FUNCTION, identifier), parse_statements(), None, None
    )


def declaration_statement() -> ASTNode:
    """Parse a declaration statement

    Raises:
        EccoInternalTypeError: If an incorrect Token value is encountered
    """
    from .statement import match_token, match_type
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK

    num = match_type()

    ident = match_token(TokenType.IDENTIFIER)[0]
    if not isinstance(ident, str):
        raise EccoInternalTypeError(
            "str",
            str(type(GLOBAL_SCANNER.current_token.value)),
            "ecco/parsing/declaration.py:declaration_statement",
        )

    arr_type: Optional[Array] = None
    if GLOBAL_SCANNER.current_token.type == TokenType.LEFT_BRACKET:
        match_token(TokenType.LEFT_BRACKET)

        if GLOBAL_SCANNER.current_token.type == TokenType.INTEGER_LITERAL:
            arr_type = Array(num, int(GLOBAL_SCANNER.current_token.value))
            match_token(TokenType.INTEGER_LITERAL)
        else:
            # We will add another case for something like arr[] = {0, 1, 2};
            # when we add initializer lists
            raise EccoArrayError("Arrays must be declared with a constant size")

        match_token(TokenType.RIGHT_BRACKET)

    ident_type: Union[Array, Number] = arr_type if arr_type else num

    # num.pointer_depth += 1
    SYMBOL_TABLE_STACK.LST[ident] = SymbolTableEntry(
        ident, Type(num.ntype.to_tokentype(), ident_type)
    )

    ste = SYMBOL_TABLE_STACK.LST[ident]
    if ste and type(ste.identifier_type.contents) in [Number, Array]:
        return ASTNode(Token(TokenType.VAR_DECL, ident), tree_type=ident_type)
        # llvm_declare_global(ident, 0, num)
        # ste.latest_llvmvalue = llvm_declare_local(ident, 0, num)
    else:
        raise EccoIdentifierError("Failed to insert identifier into LST")


def struct_declaration_statement() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK
    from .statement import match_token, match_type

    match_token(TokenType.STRUCT)
    identifier = str(match_token(TokenType.IDENTIFIER)[0])

    match_token(TokenType.LEFT_BRACE)

    arguments = OrderedDict()
    while GLOBAL_SCANNER.current_token.type != TokenType.RIGHT_BRACE:
        arg_type = match_type()
        arg_name = str(match_token(TokenType.IDENTIFIER)[0])
        match_token(TokenType.SEMICOLON)

        arguments[arg_name] = arg_type

    SYMBOL_TABLE_STACK.GST[identifier] = SymbolTableEntry(
        identifier, Type(TokenType.STRUCT, Struct(arguments))
    )

    match_token(TokenType.RIGHT_BRACE)
    match_token(TokenType.SEMICOLON)

    return ASTNode(Token(TokenType.STRUCT, identifier))


def global_declaration() -> ASTNode:
    from ..ecco import GLOBAL_SCANNER

    if GLOBAL_SCANNER.current_token.type == TokenType.STRUCT:
        return struct_declaration_statement()
    
    return function_declaration_statement()

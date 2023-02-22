from typing import List, TextIO, Optional

from ..parsing import ASTNode
from ..scanning import TokenType
from ..utils import (
    EccoFatalException,
    EccoFileError,
    LogLevel,
    log,
    EccoInternalTypeError,
)
from .llvmstackentry import LLVMStackEntry
from .llvmvalue import LLVMValue, LLVMValueType
import tempfile

LLVM_OUT_FILE: TextIO
LLVM_GLOBALS_FILE: TextIO
LLVM_VIRTUAL_REGISTER_NUMBER: int
LLVM_FREE_REGISTERS: List[int]
LLVM_LOADED_REGISTERS: List[LLVMValue]
LLVM_LABEL_INDEX: int


def translate_init():
    """Initialize values before translation

    Raises:
        EccoFileError: Raised if an error occurs while opening the output LLVM
                       file
    """
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_FREE_REGISTERS, LLVM_LOADED_REGISTERS, LLVM_GLOBALS_FILE, LLVM_LABEL_INDEX
    from ..ecco import ARGS

    try:
        LLVM_OUT_FILE = open(ARGS.output, "w+")
    except Exception as e:
        raise EccoFileError(str(e))

    try:
        LLVM_GLOBALS_FILE = tempfile.TemporaryFile(mode="w+")
    except Exception as e:
        raise EccoFileError(str(e))

    LLVM_VIRTUAL_REGISTER_NUMBER = 0

    LLVM_FREE_REGISTERS = []

    LLVM_LOADED_REGISTERS = []

    LLVM_LABEL_INDEX = 0


def translate_reinit():
    global LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_FREE_REGISTERS, LLVM_LOADED_REGISTERS

    LLVM_VIRTUAL_REGISTER_NUMBER = 0
    LLVM_FREE_REGISTERS = []
    LLVM_LOADED_REGISTERS = []


def get_next_label() -> LLVMValue:
    global LLVM_LABEL_INDEX
    LLVM_LABEL_INDEX += 1
    return LLVMValue(LLVMValueType.LABEL, LLVM_LABEL_INDEX)


def get_next_local_virtual_register() -> int:
    global LLVM_VIRTUAL_REGISTER_NUMBER
    LLVM_VIRTUAL_REGISTER_NUMBER += 1
    return LLVM_VIRTUAL_REGISTER_NUMBER


def determine_binary_expression_stack_allocation(root: ASTNode) -> List[LLVMStackEntry]:
    """Function to determine the necessary stack allocation for a binary
    expression

    Args:
        root (ASTNode): ASTNode storing binary expression

    Returns:
        List[LLVMStackEntry]: List of LLVMStackEntries describing required
                              allocated registers
    """
    global LLVM_FREE_REGISTERS
    from .llvm import get_next_local_virtual_register

    left_entry: List[LLVMStackEntry] = []
    right_entry: List[LLVMStackEntry] = []

    if root.left or root.right:
        if root.left:
            left_entry = determine_binary_expression_stack_allocation(root.left)
        if root.right:
            right_entry = determine_binary_expression_stack_allocation(root.right)

        return left_entry + right_entry
    elif root.type in [TokenType.INTEGER_LITERAL, TokenType.IDENTIFIER]:
        out_entry = LLVMStackEntry(
            LLVMValue(
                LLVMValueType.VIRTUAL_REGISTER,
                get_next_local_virtual_register(),
            ),
            4,
        )
        LLVM_FREE_REGISTERS.append(out_entry.register.int_value)
        return [out_entry]

    return []


def if_ast_to_llvm(root: ASTNode) -> LLVMValue:
    from .llvm import get_next_label, llvm_jump, llvm_label

    end_label: LLVMValue

    false_label: LLVMValue = get_next_label()
    if root.right:
        end_label = get_next_label()

    if root.left and root.middle:
        ast_to_llvm(root.left, false_label, root.type)
        ast_to_llvm(root.middle, LLVMValue(LLVMValueType.NONE), root.type)
    else:
        raise EccoInternalTypeError(
            "ASTNode with left, middle, and right children",
            "ASTNode missing left or middle child",
            "translate.py:if_ast_to_llvm",
        )

    if root.right:
        llvm_jump(end_label)
    else:
        llvm_jump(false_label)

    llvm_label(false_label)

    if root.right:
        ast_to_llvm(root.right, LLVMValue(LLVMValueType.NONE), root.type)

        llvm_jump(end_label)
        llvm_label(end_label)

    return LLVMValue(LLVMValueType.NONE)


def while_ast_to_llvm(root: ASTNode) -> LLVMValue:
    from .llvm import get_next_label, llvm_jump, llvm_label

    condition_label: LLVMValue = get_next_label()
    end_label: LLVMValue = get_next_label()

    # We have to jump because LLVM doesn't allow for any fallthroughs
    llvm_jump(condition_label)
    llvm_label(condition_label)

    ast_to_llvm(root.left, end_label, root.type)
    ast_to_llvm(root.right, LLVMValue(LLVMValueType.NONE), root.type)

    llvm_jump(condition_label)
    llvm_label(end_label)

    return LLVMValue(LLVMValueType.NONE)


def ast_to_llvm(
    root: Optional[ASTNode], rvalue: LLVMValue, parent_operation: TokenType
) -> LLVMValue:
    """Function to traverse an AST and generate LLVM code for it

    Args:
        root (ASTNode): Root ASTNode of program to generate
        rvalue (LLVMValue): Value passed from left-branch traversals to the
                            right branch
        parent_operation (TokenType): TokenType of parent of root

    Raises:
        EccoFatalException: If an unexpected Token is encountered

    Returns:
        LLVMValue: LLVMValue containing register number of expression value to
                   print
    """
    if not root:
        return LLVMValue(LLVMValueType.NONE)

    from .llvm import (
        llvm_binary_arithmetic,
        llvm_ensure_registers_loaded,
        llvm_store_constant,
        llvm_load_global,
        llvm_store_global,
        llvm_print_int,
        llvm_comparison,
        llvm_compare_jump,
        llvm_function_preamble,
        llvm_function_postamble,
        llvm_stack_allocation,
        llvm_return,
        # llvm_call_function,
    )

    left_vr: LLVMValue
    right_vr: LLVMValue

    # Special kinds of TokenTypes that shouldn't have their left and right
    # children generated in the standard manner
    if root.type == TokenType.IF:
        return if_ast_to_llvm(root)
    elif root.type == TokenType.WHILE:
        return while_ast_to_llvm(root)
    elif root.type == TokenType.AST_GLUE:
        ast_to_llvm(root.left, LLVMValue(LLVMValueType.NONE), root.type)
        ast_to_llvm(root.middle, LLVMValue(LLVMValueType.NONE), root.type)
        ast_to_llvm(root.right, LLVMValue(LLVMValueType.NONE), root.type)
        return LLVMValue(LLVMValueType.NONE)
    elif root.type == TokenType.FUNCTION:
        if type(root.token.value) != str:
            raise EccoInternalTypeError(
                "str", str(type(root.token.value)), "translate.py:ast_to_llvm"
            )
        llvm_function_preamble(root.token.value)
        llvm_stack_allocation(determine_binary_expression_stack_allocation(root))
        ast_to_llvm(root.left, LLVMValue(LLVMValueType.NONE), root.type)
        llvm_function_postamble()
        return LLVMValue(LLVMValueType.NONE)

    if root.left:
        left_vr = ast_to_llvm(root.left, LLVMValue(LLVMValueType.NONE), root.type)
    if root.right:
        right_vr = ast_to_llvm(root.right, left_vr, root.type)

    # Binary arithmetic
    if root.token.is_binary_arithmetic():
        left_vr, right_vr = llvm_ensure_registers_loaded([left_vr, right_vr])
        return llvm_binary_arithmetic(root.token, left_vr, right_vr)
    # Comparison operators
    elif root.token.is_comparison_operator():
        left_vr, right_vr = llvm_ensure_registers_loaded([left_vr, right_vr])
        if parent_operation in [TokenType.IF, TokenType.WHILE]:
            return llvm_compare_jump(root.token, left_vr, right_vr, rvalue)
        else:
            return llvm_comparison(root.token, left_vr, right_vr)
    # Terminal Node
    elif root.token.is_terminal():
        if root.type == TokenType.INTEGER_LITERAL:
            return llvm_store_constant(int(root.token.value))
    # Rvalue Identifier
    elif root.type == TokenType.IDENTIFIER:
        return llvm_load_global(str(root.token.value))
    # Lvalue Identifier
    elif root.type == TokenType.LEFTVALUE_IDENTIFIER:
        llvm_store_global(str(root.token.value), rvalue)
        return rvalue
    elif root.type == TokenType.ASSIGN:
        return rvalue
    # Return statement
    elif root.type == TokenType.RETURN:
        if type(root.token.value) != str:
            raise EccoInternalTypeError(
                "str", str(type(root.token.value)), "translate.py:ast_to_llvm"
            )
        llvm_return(left_vr, root.token.value)
        return LLVMValue(LLVMValueType.NONE)
    # Function call
    elif root.type == TokenType.FUNCTION_CALL:
        pass
        # return llvm_call_function(left_vr, root.token.value)
    # Print statement
    elif root.type == TokenType.PRINT:
        llvm_print_int(left_vr)
    else:
        raise EccoFatalException(
            "", f'Unknown token encountered in ast_to_llvm: "{str(root.token)}"'
        )

    return LLVMValue(LLVMValueType.NONE, None)


def generate_llvm() -> None:
    """Abstraction function for generating LLVM for a program"""
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_GLOBALS_FILE

    translate_init()

    from .llvm import (
        llvm_preamble,
        llvm_postamble,
    )
    from ..parsing import function_declaration_statement
    from ..ecco import GLOBAL_SCANNER

    llvm_preamble()

    while GLOBAL_SCANNER.current_token.type != TokenType.EOF:
        translate_reinit()
        root = function_declaration_statement()
        ast_to_llvm(root, LLVMValue(LLVMValueType.NONE), root.type)

    llvm_postamble()

    from .clang import link_llvm_globals

    link_llvm_globals()

    if not LLVM_OUT_FILE.closed:
        LLVM_OUT_FILE.close()

    if not LLVM_GLOBALS_FILE.closed:
        LLVM_GLOBALS_FILE.close()

    log(LogLevel.DEBUG, f"LLVM written to {LLVM_OUT_FILE.name}")

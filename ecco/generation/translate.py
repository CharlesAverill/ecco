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
LLVM_LABEL_INDEX: int


def translate_init():
    """Initialize values before translation

    Raises:
        EccoFileError: Raised if an error occurs while opening the output LLVM
                       file
    """
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_FREE_REGISTERS, LLVM_GLOBALS_FILE, LLVM_LABEL_INDEX
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

    LLVM_LABEL_INDEX = 0


def translate_reinit():
    global LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_FREE_REGISTERS

    LLVM_VIRTUAL_REGISTER_NUMBER = 0
    LLVM_FREE_REGISTERS = []


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
    from ..ecco import ARGS

    left_entry: List[LLVMStackEntry] = []
    middle_entry: List[LLVMStackEntry] = []
    right_entry: List[LLVMStackEntry] = []

    if root.left or root.right:
        if root.left:
            left_entry = determine_binary_expression_stack_allocation(root.left)
        if root.middle:
            middle_entry = determine_binary_expression_stack_allocation(root.middle)
        if root.right:
            right_entry = determine_binary_expression_stack_allocation(root.right)

        return left_entry + middle_entry + right_entry
    elif root.type in [TokenType.INTEGER_LITERAL, TokenType.IDENTIFIER]:
        if ARGS.opt != 0:
            return []

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
    root: Optional[ASTNode], label: LLVMValue, parent_operation: TokenType
) -> LLVMValue:
    """Function to traverse an AST and generate LLVM code for it

    Args:
        root (ASTNode): Root ASTNode of program to generate
        label (LLVMValue): Label value passed from left-branch traversals to the
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
        llvm_call_function,
        llvm_get_address,
        llvm_dereference,
        llvm_store_dereference,
        llvm_store_local,
    )

    from ..ecco import ARGS, GLOBAL_SYMBOL_TABLE, SYMBOL_TABLE_STACK

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
        llvm_function_postamble(root.token.value)
        return LLVMValue(LLVMValueType.NONE)

    if root.left:
        left_vr = ast_to_llvm(root.left, LLVMValue(LLVMValueType.NONE), root.type)
    if root.right:
        right_vr = ast_to_llvm(root.right, LLVMValue(LLVMValueType.NONE), root.type)

    # Binary arithmetic
    if root.token.is_binary_arithmetic():
        left_vr, right_vr = llvm_ensure_registers_loaded([left_vr, right_vr])
        return llvm_binary_arithmetic(root.token, left_vr, right_vr)
    # Comparison operators
    elif root.token.is_comparison_operator():
        left_vr, right_vr = llvm_ensure_registers_loaded([left_vr, right_vr])
        if parent_operation in [TokenType.IF, TokenType.WHILE]:
            return llvm_compare_jump(root.token, left_vr, right_vr, label)
        else:
            return llvm_comparison(root.token, left_vr, right_vr)
    # Terminal Node
    elif root.token.is_terminal():
        if root.type == TokenType.INTEGER_LITERAL:
            if ARGS.opt != 0:
                return LLVMValue(
                    LLVMValueType.CONSTANT, int(root.token.value), root.tree_type.ntype
                )
            return llvm_store_constant(int(root.token.value))
    # Rvalue Identifier
    elif root.type == TokenType.IDENTIFIER:
        if root.is_rvalue or parent_operation == TokenType.DEREFERENCE:
            if GLOBAL_SYMBOL_TABLE[str(root.token.value)]:
                return llvm_load_global(str(root.token.value))
            else:
                ste = SYMBOL_TABLE_STACK[str(root.token.value)]
                if ste:
                    return ste.latest_llvmvalue
                else:
                    raise EccoInternalTypeError(
                        "STE with LLVMValue",
                        "STE without LLVMValue",
                        "translate.py:ast_to_llvm",
                    )
        else:
            return LLVMValue(LLVMValueType.NONE)
    elif root.type == TokenType.ASSIGN:
        if root.right:
            if root.right.type == TokenType.IDENTIFIER:
                if GLOBAL_SYMBOL_TABLE[str(root.right.token.value)]:
                    llvm_store_global(str(root.right.token.value), left_vr)
                    return left_vr
                else:
                    llvm_store_local(
                        SYMBOL_TABLE_STACK[str(root.right.token.value)], left_vr
                    )
                    return left_vr
            elif root.right.type == TokenType.DEREFERENCE:
                llvm_store_dereference(right_vr, left_vr)
                return left_vr

            raise EccoInternalTypeError(
                "Identifier or Dereference token",
                str(root.right.type),
                "translate.py:ast_to_llvm",
            )
        raise EccoInternalTypeError(
            "two children", "nothing", "translate.py:ast_to_llvm"
        )
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
        passed_llvmvalues = []
        for passed_arg in root.function_call_arguments:
            passed_llvmvalues.append(
                ast_to_llvm(
                    passed_arg, LLVMValue(LLVMValueType.NONE), TokenType.FUNCTION_CALL
                )
            )
        return llvm_call_function(passed_llvmvalues, str(root.token.value))
    elif root.type == TokenType.AMPERSAND:
        return llvm_get_address(str(root.token.value))
    elif root.type == TokenType.DEREFERENCE:
        if root.is_rvalue:
            return llvm_dereference(left_vr)
        else:
            return left_vr
    # Print statement
    elif root.type == TokenType.PRINT:
        llvm_print_int(left_vr)
    # Catch-all
    elif root.type == TokenType.UNKNOWN_TOKEN:
        pass
    else:
        raise EccoFatalException(
            "", f'Unknown token encountered in ast_to_llvm: "{str(root.token)}"'
        )

    return LLVMValue(LLVMValueType.NONE)


def generate_llvm() -> None:
    """Abstraction function for generating LLVM for a program"""
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_GLOBALS_FILE

    translate_init()

    from .llvm import (
        llvm_preamble,
        llvm_postamble,
    )
    from ..parsing import function_declaration_statement
    from ..ecco import GLOBAL_SCANNER, SYMBOL_TABLE_STACK

    llvm_preamble()

    while GLOBAL_SCANNER.current_token.type != TokenType.EOF:
        translate_reinit()
        SYMBOL_TABLE_STACK.push()
        root = function_declaration_statement()
        ast_to_llvm(root, LLVMValue(LLVMValueType.NONE), root.type)
        SYMBOL_TABLE_STACK.pop()

    llvm_postamble()

    from .clang import link_llvm_globals

    link_llvm_globals()

    if not LLVM_OUT_FILE.closed:
        LLVM_OUT_FILE.close()

    if not LLVM_GLOBALS_FILE.closed:
        LLVM_GLOBALS_FILE.close()

    log(LogLevel.DEBUG, f"LLVM written to {LLVM_OUT_FILE.name}")

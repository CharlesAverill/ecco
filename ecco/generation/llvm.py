from typing import List, Optional

from ..scanning import Token, TokenType
from ..utils import EccoFatalException, EccoInternalTypeError, EccoIdentifierError
from .llvmstackentry import LLVMStackEntry
from .symboltable import SymbolTableEntry
from .llvmvalue import LLVMValue, LLVMValueType
from .types import NumberType, Function, Number
from ..ecco import ARGS, GLOBAL_SYMBOL_TABLE
from .translate import (
    add_loaded_register,
    get_last_loaded_register,
    LLVM_OUT_FILE,
    get_next_local_virtual_register,
    LLVM_GLOBALS_FILE,
    get_next_label,
)

NEWLINE = "\n"
TAB = "\t"

LLVM_GLOBALS_PLACEHOLDER = (
    "<ECCO GLOBALS PLACEHOLDER - If you see this, an issue with ECCO occurrred!>"
)


def llvm_preamble():
    """Generates the preamble of the LLVM program"""
    LLVM_OUT_FILE.writelines(
        [
            f"; ModuleID = '{ARGS.PROGRAM}'",
            NEWLINE,
            f'source_filename = "{ARGS.PROGRAM}"',
            NEWLINE,
            'target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"',
            NEWLINE,
            'target triple = "x86_64-pc-linux-gnu"',
            NEWLINE,
            NEWLINE,
            '@print_int_fstring = private unnamed_addr constant [4 x i8] c"%d\\0A\\00", align 1',
            NEWLINE,
            LLVM_GLOBALS_PLACEHOLDER,
            NEWLINE,
            NEWLINE,
            "; Function Attrs: noinline nounwind optnone uwtable",
            NEWLINE,
        ]
    )


def llvm_postamble():
    """Generates the postamble of the LLVM program"""
    LLVM_OUT_FILE.writelines(
        [
            "declare i32 @printf(i8*, ...) #1",
            NEWLINE,
            'attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }',
            NEWLINE,
            'attributes #1 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }',
            NEWLINE,
            "!llvm.module.flags = !{!0, !1, !2, !3, !4}",
            NEWLINE,
            "!llvm.ident = !{!5}",
            NEWLINE,
            NEWLINE,
            '!0 = !{i32 1, !"wchar_size", i32 4}',
            NEWLINE,
            '!1 = !{i32 7, !"PIC Level", i32 2}',
            NEWLINE,
            '!2 = !{i32 7, !"PIE Level", i32 2}',
            NEWLINE,
            '!3 = !{i32 7, !"uwtable", i32 1}',
            NEWLINE,
            '!4 = !{i32 7, !"frame-pointer", i32 2}',
            NEWLINE,
            '!5 = !{!"Ubuntu clang version 10.0.0-4ubuntu1"}',
            NEWLINE,
        ]
    )


def llvm_ensure_registers_loaded(
    registers_to_check: List[LLVMValue],
) -> List[LLVMValue]:
    """Checks if the provided registers are loaded. If not, they will be loaded
    and the new register values will be returned.  If none of or only some of
    the input registers are loaded, the already-loaded registers will be
    returned regardless

    Args:
        registers_to_check (List[LLVMValue]): A list of LLVMValues containing
                                              register numbers to check for
                                              loadedness

    Returns:
        List[LLVMValue]: A list of LLVMValues containing loaded register numbers
                         corresponding to the input registers
    """
    from .translate import LLVM_LOADED_REGISTERS

    found_registers: List[bool] = [False] * len(registers_to_check)

    # Check if our input registers are loaded
    for loaded_register in LLVM_LOADED_REGISTERS:
        for i, reg in enumerate(registers_to_check):
            # Mark as loaded
            if reg.int_value == loaded_register.int_value:
                found_registers[i] = True

            # If all of our registers are loaded, we can just return them
            if found_registers.count(True) == len(registers_to_check):
                return registers_to_check

    # Load any unloaded registers
    loaded_registers: List[LLVMValue] = []
    for i in range(len(registers_to_check)):
        if not found_registers[i]:
            new_reg = get_next_local_virtual_register()
            loaded_registers.append(
                LLVMValue(
                    LLVMValueType.VIRTUAL_REGISTER,
                    new_reg,
                    registers_to_check[i].number_type,
                )
            )
            LLVM_OUT_FILE.writelines(
                [
                    TAB,
                    f"%{new_reg} = load {registers_to_check[i].number_type}, {registers_to_check[i].number_type}* %{registers_to_check[i].int_value}",
                    NEWLINE,
                ]
            )
            add_loaded_register((loaded_registers[-1]))
        else:
            loaded_registers.append(registers_to_check[i])

    return loaded_registers


def llvm_int_resize(register: LLVMValue, new_width: NumberType):
    register = llvm_ensure_registers_loaded([register])[0]

    op = "zext" if int(new_width) > int(register.number_type.byte_width) else "trunc"

    out_reg_num = get_next_local_virtual_register()

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_reg_num} = {op} {register.number_type} %{register.int_value} to {new_width}",
            NEWLINE,
        ]
    )

    add_loaded_register(
        LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_reg_num, new_width)
    )

    return get_last_loaded_register()


def llvm_add(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    """Perform an addition operation

    Args:
        left_vr (LLVMValue): Virtual register number containing the value on
                             the left of the addition symbol
        right_vr (LLVMValue): Virtual register number containing the value on
                              the right of the addition symbol

    Returns:
        LLVMValue: LLVMValue containing the register number of the sum of the
                   contents of left_vr and right_vr
    """
    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = add nsw {left_vr.number_type} %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr, left_vr.number_type)


def llvm_sub(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    """Perform a subtraction operation

    Args:
        left_vr (LLVMValue): Virtual register number containing the value on
                             the left of the subtraction symbol
        right_vr (LLVMValue): Virtual register number containing the value on
                              the right of the subtraction symbol

    Returns:
        LLVMValue: LLVMValue containing the register number of the difference
                   of the contents of left_vr and right_vr
    """
    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = sub nsw {left_vr.number_type} %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr, left_vr.number_type)


def llvm_mul(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    """Perform a multiplication operation

    Args:
        left_vr (LLVMValue): Virtual register number containing the value on
                             the left of the multiplication symbol
        right_vr (LLVMValue): Virtual register number containing the value on
                              the right of the multiplication symbol

    Returns:
        LLVMValue: LLVMValue containing the register number of the product of
                   the contents of left_vr and right_vr
    """
    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = mul nsw {left_vr.number_type} %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr, left_vr.number_type)


def llvm_div(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    """Perform an integer division operation

    Args:
        left_vr (LLVMValue): Virtual register number containing the value on
                             the left of the division symbol
        right_vr (LLVMValue): Virtual register number containing the value on
                              the right of the division symbol

    Returns:
        LLVMValue: LLVMValue containing the register number of the quotient of
                   the contents of left_vr and right_vr
    """
    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = udiv {left_vr.number_type} %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr, left_vr.number_type)


def llvm_binary_arithmetic(
    token: Token, left_vr: LLVMValue, right_vr: LLVMValue
) -> LLVMValue:
    """Abstraction function to generate LLVM for binary arithmetic expressions

    Args:
        token (Token): Token containing the operation type
        left_vr (LLVMValue): Virtual register number containing the value on
                             the left of the operator
        right_vr (LLVMValue): Virtual register number containing the value on
                              the right of the operator

    Raises:
        EccoFatalException: If the passed Token is not a binary arithmetic
                            operator

    Returns:
        LLVMValue: LLVMValue containing the register number of the result of
                   the binary operation on left_vr and right_vr - this register
                   is guaranteed to be loaded
    """
    out_vr: LLVMValue

    if int(left_vr.number_type) < int(right_vr.number_type):
        left_vr = llvm_int_resize(left_vr, right_vr.number_type)
    elif int(left_vr.number_type) > int(right_vr.number_type):
        right_vr = llvm_int_resize(right_vr, left_vr.number_type)

    if token.type == TokenType.PLUS:
        out_vr = llvm_add(left_vr, right_vr)
    elif token.type == TokenType.MINUS:
        out_vr = llvm_sub(left_vr, right_vr)
    elif token.type == TokenType.STAR:
        out_vr = llvm_mul(left_vr, right_vr)
    elif token.type == TokenType.SLASH:
        out_vr = llvm_div(left_vr, right_vr)
    else:
        raise EccoFatalException(
            "",
            f'llvm_binary_arithmetic receieved non-binary-arithmetic-operator Token "{str(token.type)}"',
        )

    add_loaded_register((out_vr))

    return out_vr


def llvm_comparison(token: Token, left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    out_vr: LLVMValue

    if int(left_vr.number_type) < int(right_vr.number_type):
        left_vr = llvm_int_resize(left_vr, right_vr.number_type)
    elif int(left_vr.number_type) > int(right_vr.number_type):
        right_vr = llvm_int_resize(right_vr, left_vr.number_type)

    llvm_cmp_operators: List[str] = ["eq", "ne", "slt", "sle", "sgt", "sge"]

    try:
        operator: str = llvm_cmp_operators[int(token.type) - int(TokenType.EQ)]
    except IndexError:
        raise EccoFatalException(
            "",
            f'llvm_comparison received non-comparison-operator Token "{str(token.type)}"',
        )

    out_vr = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        get_next_local_virtual_register(),
        NumberType.BOOL,
    )

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr.int_value} = icmp {operator} {left_vr.number_type} %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    add_loaded_register((out_vr))

    return out_vr


def llvm_store_constant(value: int) -> LLVMValue:
    """Store a constant value

    Args:
        value (int): Constant to be stored

    Returns:
        LLVMValue: LLVMValue containing the register number of the stored
                   constant. This register is NOT confirmed to be loaded
    """
    from .translate import LLVM_FREE_REGISTERS

    store_reg = LLVM_FREE_REGISTERS.pop()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"store i32 {value}, i32* %{store_reg}",
            NEWLINE,
        ]
    )

    return LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        store_reg,
    )


def llvm_declare_global(name: str, value: int = 0, ntype: NumberType = NumberType.INT):
    """Declare a global variable

    Args:
        name (str): Name of global variable
        value (int, optional): Value to set variable to. Defaults to 0.
    """
    LLVM_GLOBALS_FILE.writelines([f"@{name} = global {ntype} {value}", NEWLINE])


def llvm_load_global(name: str) -> LLVMValue:
    """Load a global variable

    Args:
        name (str): Name of variable to load

    Returns:
        LLVMValue: LLVMValue containing the register number the variable was loaded into
    """
    out_vr: int = get_next_local_virtual_register()

    ste = GLOBAL_SYMBOL_TABLE[name]
    if ste and type(ste.identifier_type.contents) == Number:
        glob_ntype = ste.identifier_type.contents.ntype

    LLVM_OUT_FILE.writelines(
        [TAB, f"%{out_vr} = load {glob_ntype}, {glob_ntype}* @{name}", NEWLINE]
    )

    add_loaded_register(LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr, glob_ntype))

    return get_last_loaded_register()


def llvm_store_global(name: str, rvalue: LLVMValue):
    """Store a value into a global variable

    Args:
        name (str): Global variable to store into
        rvalue_reg (int): Register containing the contents to store into the variable
    """
    ste = GLOBAL_SYMBOL_TABLE[name]
    if ste:
        if (
            type(ste.identifier_type.contents) == Number
            and rvalue.number_type != ste.identifier_type.contents.ntype
        ):
            rvalue = llvm_int_resize(rvalue, ste.identifier_type.contents.ntype)
    else:
        raise EccoFatalException(
            "",
            f"Undeclared identifier {name} was allowed to propagate to LLVM generation",
        )

    rvalue.int_value = llvm_ensure_registers_loaded([rvalue])[0].int_value

    if type(ste.identifier_type.contents) == Number:
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                f"store {rvalue.number_type} %{rvalue.int_value}, {ste.identifier_type.contents.ntype}* @{name}",
                NEWLINE,
            ]
        )
    else:
        raise EccoInternalTypeError(
            str(Number),
            str(type(ste.identifier_type.contents)),
            "llvm.py:llvm_store_global",
        )


def llvm_stack_allocation(entries: List[LLVMStackEntry]):
    """Generate allocation statements

    Args:
        entries (List[LLVMStackEntry]): List of LLVMStackEntries that describe
                                        the requirements of an expression.
    """
    for entry in entries:
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                f"%{entry.register.int_value} = alloca i32, align {entry.align_bytes}",
                NEWLINE,
            ]
        )

    return True


def llvm_print_int(reg: LLVMValue) -> None:
    """Print out an integer followed by a newline and a null terminator

    Args:
        reg (LLVMValue): LLVMValue containing the register number of the
                         integer to print
    """
    reg = llvm_ensure_registers_loaded([reg])[0]

    get_next_local_virtual_register()

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @print_int_fstring , i32 0, i32 0), {reg.number_type} %{reg.int_value})",
            NEWLINE,
        ]
    )


PURPLE_LABEL_PREFIX: str = "L"


def llvm_label(label: LLVMValue) -> None:
    if label.value_type != LLVMValueType.LABEL:
        raise EccoInternalTypeError(
            f"{LLVMValueType.LABEL}", f"{label.value_type}", "llvm.py:llvm_label"
        )

    LLVM_OUT_FILE.writelines([TAB, f"{PURPLE_LABEL_PREFIX}{label.int_value}:", NEWLINE])


def llvm_jump(label: LLVMValue) -> None:
    if label.value_type != LLVMValueType.LABEL:
        raise EccoInternalTypeError(
            f"{LLVMValueType.LABEL}", f"{label.value_type}", "llvm.py:llvm_jump"
        )

    LLVM_OUT_FILE.writelines(
        [TAB, f"br label %{PURPLE_LABEL_PREFIX}{label.int_value}", NEWLINE]
    )


def llvm_conditional_jump(
    condition_register: LLVMValue, true_label: LLVMValue, false_label: LLVMValue
) -> None:
    if true_label.value_type != LLVMValueType.LABEL:
        raise EccoInternalTypeError(
            f"{LLVMValueType.LABEL}",
            f"{true_label.value_type}",
            "llvm.py:llvm_conditional_jump",
        )
    if false_label.value_type != LLVMValueType.LABEL:
        raise EccoInternalTypeError(
            f"{LLVMValueType.LABEL}",
            f"{false_label.value_type}",
            "llvm.py:llvm_conditional_jump",
        )

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"br {condition_register.number_type} %{condition_register.int_value}, label %{PURPLE_LABEL_PREFIX}{true_label.int_value}, label %{PURPLE_LABEL_PREFIX}{false_label.int_value}",
            NEWLINE,
        ]
    )


def llvm_compare_jump(
    comparison_type: Token,
    left_vr: LLVMValue,
    right_vr: LLVMValue,
    false_label: LLVMValue,
) -> LLVMValue:
    comparison_result: LLVMValue = llvm_comparison(comparison_type, left_vr, right_vr)

    true_label: LLVMValue = get_next_label()

    llvm_conditional_jump(comparison_result, true_label, false_label)

    llvm_label(true_label)

    return comparison_result


def llvm_function_preamble(function_name: str) -> None:
    from .symboltable import SymbolTableEntry

    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoFatalException(
            "", "Tried to generate function preamble for undeclared function"
        )
    elif entry.identifier_type.type != Function:
        raise EccoInternalTypeError(
            "Function",
            str(entry.identifier_type.type),
            "llvm.py:llvm_function_preamble",
        )

    LLVM_OUT_FILE.writelines(
        [
            f"define dso_local {entry.identifier_type.llvm_repr} @{function_name}() #0 {{",
            NEWLINE,
        ]
    )


def llvm_function_postamble(function_name: str) -> None:
    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to close undeclared function "{function_name}"'
        )
    elif type(entry.identifier_type.contents) != Function:
        raise EccoFatalException(
            "",
            f'Tried to close non-function identifier "{function_name}"',
        )

    LLVM_OUT_FILE.writelines([TAB, "ret "])

    if entry.identifier_type.contents.return_type == TokenType.VOID:
        LLVM_OUT_FILE.write("void")
    else:
        LLVM_OUT_FILE.writelines(
            [
                f"{NumberType.from_tokentype(entry.identifier_type.contents.return_type)} {'' if entry.identifier_type.contents.return_type == TokenType.VOID else '0'}",
                NEWLINE,
            ]
        )

    LLVM_OUT_FILE.writelines(["}", NEWLINE])


def llvm_return(return_value: LLVMValue, function_name: str) -> None:
    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to return for undeclared function "{function_name}"'
        )
    elif type(entry.identifier_type.contents) != Function:
        raise EccoFatalException(
            "",
            f'Tried to generate return statement for non-function identifier "{function_name}"',
        )

    if entry.identifier_type.contents.return_type == TokenType.VOID:
        LLVM_OUT_FILE.writelines([TAB, "ret void", NEWLINE])
    else:
        return_value = llvm_ensure_registers_loaded([return_value])[0]
        LLVM_OUT_FILE.writelines(
            [TAB, f"ret {return_value.number_type} %{return_value.int_value}", NEWLINE]
        )
        
    get_next_local_virtual_register()


def llvm_call_function(argument: LLVMValue, function_name: str) -> LLVMValue:
    out: LLVMValue = LLVMValue(LLVMValueType.NONE)

    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to generate call for undeclared function "{function_name}"'
        )
    elif type(entry.identifier_type.contents) != Function:
        raise EccoFatalException(
            "",
            f'Tried to call non-function identifier "{function_name}" as function',
        )

    LLVM_OUT_FILE.write(TAB)

    call_type: str = "void"
    if entry.identifier_type.contents.return_type != TokenType.VOID:
        out = LLVMValue(
            LLVMValueType.VIRTUAL_REGISTER,
            get_next_local_virtual_register(),
            NumberType.from_tokentype(entry.identifier_type.contents.return_type),
        )
        LLVM_OUT_FILE.writelines([f"%{out.int_value} = "])
        call_type = str(out.number_type)
        add_loaded_register((out))

    LLVM_OUT_FILE.writelines([f"call {call_type} () @{function_name}()", NEWLINE])

    return out

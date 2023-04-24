from typing import List, Optional, Union

from ..scanning import Token, TokenType
from ..utils import EccoFatalException, EccoInternalTypeError, EccoIdentifierError
from .llvmstackentry import LLVMStackEntry
from .symboltable import SymbolTableEntry
from .llvmvalue import LLVMValue, LLVMValueType
from .types import NumberType, Function, Number, Array, Struct, EccoUnion
from ..ecco import ARGS, GLOBAL_SYMBOL_TABLE, SYMBOL_TABLE_STACK
from .translate import (
    LLVM_OUT_FILE,
    get_next_local_virtual_register,
    LLVM_GLOBALS_FILE,
    get_next_label,
)

NEWLINE = "\n"
TAB = "\t"

LLVM_GLOBALS_PLACEHOLDER = (
    "<ECCO GLOBALS PLACEHOLDER - If you see this, an issue with ECCO occurred!>"
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
            "define dso_local i32 @printint(i32 %value) {",
            NEWLINE,
            TAB,
            "call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @print_int_fstring , i32 0, i32 0), i32 %value)",
            NEWLINE,
            TAB,
            "ret i32 %value",
            NEWLINE,
            "}",
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
    registers_to_check: List[LLVMValue], load_level: int = 0
) -> List[LLVMValue]:
    """Checks if the provided registers are loaded. If not, they will be loaded
    and the new register values will be returned.  If none of or only some of
    the input registers are loaded, the already-loaded registers will be
    returned regardless

    Args:
        registers_to_check (List[LLVMValue]): A list of LLVMValues containing
                                              register numbers to check for
                                              loadedness
        load_level: The pointer depth to which registers should be loaded to

    Returns:
        List[LLVMValue]: A list of LLVMValues containing loaded register numbers
                         corresponding to the input registers
    """
    load_level = max(0, load_level)

    found_registers: List[bool] = [False] * len(registers_to_check)

    # Check if our input registers are loaded
    for i, reg in enumerate(registers_to_check):
        # Mark as loaded
        if reg.pointer_depth <= load_level:
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
                    registers_to_check[i].pointer_depth - 1,
                    array_type=registers_to_check[i].array,
                    struct_type=registers_to_check[i].struct,
                )
            )
            LLVM_OUT_FILE.writelines(
                [
                    TAB,
                    f"%{new_reg} = load {loaded_registers[-1].llvm_type},"
                    f" {registers_to_check[i].llvm_type} %{registers_to_check[i].register_name}",
                    NEWLINE,
                ]
            )
        else:
            loaded_registers.append(registers_to_check[i])

    return llvm_ensure_registers_loaded(loaded_registers, load_level)


def llvm_int_resize(register: LLVMValue, new_width: NumberType) -> LLVMValue:
    """Resize the contents of a virtual register using zext or trunc

    Args:
        register (LLVMValue): Register contents to resize
        new_width (NumberType): NumberType representing new bitwidth of data

    Returns:
        LLVMValue: Register containing resized data
    """
    if register.number_type == new_width:
        return register

    if register.value_type == LLVMValueType.CONSTANT:
        register.int_value = min(register.int_value, register.number_type.max_val)
        register.number_type = new_width
        return register

    register = llvm_ensure_registers_loaded([register])[0]

    op = "zext" if new_width.byte_width > register.number_type.byte_width else "trunc"

    out_reg_num = get_next_local_virtual_register()

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_reg_num} = {op} {register.number_type} %{register.register_name} to {new_width}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_reg_num, new_width)


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
            f"%{out_vr} = add nsw {left_vr.number_type} {left_vr.llvm_display_value}, {right_vr.llvm_display_value}",
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
            f"%{out_vr} = sub nsw {left_vr.number_type} {left_vr.llvm_display_value}, {right_vr.llvm_display_value}",
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
            f"%{out_vr} = mul nsw {left_vr.number_type} {left_vr.llvm_display_value}, {right_vr.llvm_display_value}",
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
            f"%{out_vr} = udiv {left_vr.number_type} {left_vr.llvm_display_value}, {right_vr.llvm_display_value}",
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

    if (
        left_vr.value_type == LLVMValueType.CONSTANT
        and right_vr.value_type == LLVMValueType.CONSTANT
    ):
        op = str(token.type)
        if op == "/":
            op = "//"
        return LLVMValue(
            LLVMValueType.CONSTANT,
            value=eval(f"{left_vr.int_value} {op} {right_vr.int_value}"),
        )

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

    return out_vr


def llvm_comparison(token: Token, left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    """Perform a relational comparison on two operands

    Args:
        token (Token): Type of comparison to perform
        left_vr (LLVMValue): Left operand
        right_vr (LLVMValue): Right operand

    Raises:
        EccoFatalException: If a non-comparison operator is provided

    Returns:
        LLVMValue: Result of comparison, i1
    """
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
            f"%{out_vr.register_name} = icmp {operator} {left_vr.llvm_repr}, {right_vr.llvm_display_value}",
            NEWLINE,
        ]
    )

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

    out = llvm_ensure_registers_loaded(
        [LLVMValue(LLVMValueType.VIRTUAL_REGISTER, store_reg, pointer_depth=1)]
    )[0]
    return out


def llvm_declare_global(
    name: str, _value: int = 0, num: Number = Number(NumberType.INT, 0)
):
    """Declare a global variable

    Args:
        name (str): Name of variable
        _value (int, optional): Value to set variable to. Defaults to 0.
        num (Number): Number object storing data type and pointer depth
    """
    value: str = "null" if num.pointer_depth - 1 > 0 else str(_value)

    LLVM_GLOBALS_FILE.writelines(
        [
            f"@{name} = global {num.ntype}{'*' * (num.pointer_depth - 1)} {value}",
            NEWLINE,
        ]
    )


def llvm_declare_local(name: str, typ: Union[Number, Array, Struct, EccoUnion]):
    """Declare a local variable

    Args:
        name (str): Name of variable
        value (int, optional): Value to set variable to. Defaults to 0.
        num (Number): Number object storing data type and pointer depth
    """
    out = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        name,
        typ.ntype,
        typ.pointer_depth,
        array_type=(typ if isinstance(typ, Array) else None),
        struct_type=(typ if isinstance(typ, Struct) else None),
        union_type=(typ if isinstance(typ, EccoUnion) else None),
    )

    llvm_stack_allocation([LLVMStackEntry(out, typ.ntype.byte_width)])

    out.pointer_depth += 1

    if isinstance(typ, Number) and typ.value != 0:
        llvm_store_local(
            out,
            LLVMValue(LLVMValueType.CONSTANT, typ.value, typ.ntype, typ.pointer_depth),
        )

    return out


def llvm_load_global(name: str) -> LLVMValue:
    """Load a global variable

    Args:
        name (str): Name of variable to load

    Returns:
        LLVMValue: LLVMValue containing the register number the variable was loaded into
    """
    ste = SYMBOL_TABLE_STACK[name]
    if not ste:
        raise EccoFatalException("", "Tried to load nonexistent global variable")
    elif not isinstance(ste.identifier_type.contents, Number):
        raise EccoInternalTypeError(
            "Number",
            str(type(ste.identifier_type.contents)),
            "llvm.py:llvm_load_global",
        )
    elif ste.is_enum_val:
        if not isinstance(ste.identifier_type.contents, Number):
            raise EccoInternalTypeError(
                "Number",
                str(type(ste.identifier_type.contents)),
                "llvm.py:llvm_load_global",
            )
        return LLVMValue(
            LLVMValueType.CONSTANT,
            ste.identifier_type.contents.value,
            ste.identifier_type.contents.ntype,
        )
    else:
        glob_ntype = ste.identifier_type.contents.ntype

    out_vr: int = get_next_local_virtual_register()

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = load {glob_ntype}{ste.identifier_type.contents.references[:-1]}, {glob_ntype}{ste.identifier_type.contents.references} @{name}",
            NEWLINE,
        ]
    )

    return LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        out_vr,
        glob_ntype,
        ste.identifier_type.contents.pointer_depth - 1,
        name,
    )


def llvm_store_global(name: str, rvalue: LLVMValue):
    """Store a value into a global variable

    Args:
        name (str): Global variable to store into
        rvalue_reg (int): Register containing the contents to store into the variable
    """
    ste = SYMBOL_TABLE_STACK[name]
    if ste:
        if (
            isinstance(ste.identifier_type.contents, Number)
            and rvalue.number_type != ste.identifier_type.contents.ntype
        ):
            rvalue = llvm_int_resize(rvalue, ste.identifier_type.contents.ntype)
    else:
        raise EccoFatalException(
            "",
            f"Undeclared identifier {name} was allowed to propagate to LLVM generation",
        )

    if ste.is_enum_val:
        raise EccoIdentifierError("Cannot assign to constant values")

    if not isinstance(ste.identifier_type.contents, Number):
        raise EccoFatalException("", "Tried to store data into non-number")

    if rvalue.value_type == LLVMValueType.VIRTUAL_REGISTER:
        rvalue = llvm_ensure_registers_loaded(
            [rvalue], ste.identifier_type.contents.pointer_depth - 1
        )[0]

        if rvalue.pointer_depth != ste.identifier_type.contents.pointer_depth - 1:
            raise EccoFatalException(
                "", "Pointer mismatch when trying to save to global variable"
            )

        if isinstance(ste.identifier_type.contents, Number):
            LLVM_OUT_FILE.writelines(
                [
                    TAB,
                    f"store {rvalue.number_type}{rvalue.references} %{rvalue.register_name}, "
                    f"{ste.identifier_type.contents.ntype}{ste.identifier_type.contents.references} @{name}",
                    NEWLINE,
                ]
            )
        else:
            raise EccoInternalTypeError(
                str(Number),
                str(type(ste.identifier_type.contents)),
                "llvm.py:llvm_store_global",
            )
    elif rvalue.value_type == LLVMValueType.CONSTANT:
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                f"store {ste.identifier_type.contents.ntype} {rvalue.int_value}, {ste.identifier_type.contents.ntype}{ste.identifier_type.contents.references} @{name}",
                NEWLINE,
            ]
        )


def llvm_store_local(
    var: Union[LLVMValue, Optional[SymbolTableEntry]], rvalue: LLVMValue
) -> None:
    """Store a value into a local variable

    Args:
        name (Union[LLVMValue, Optional[SymbolTableEntry]]): Local variable to store into
        rvalue_reg (int): Register containing the contents to store into the variable
    """
    if isinstance(var, LLVMValue) or (
        isinstance(var, SymbolTableEntry)
        and rvalue.value_type == LLVMValueType.CONSTANT
    ):
        lvar: LLVMValue = LLVMValue(LLVMValueType.NONE)
        if isinstance(var, LLVMValue):
            lvar = var
        elif isinstance(var, SymbolTableEntry):
            lvar = var.latest_llvmvalue

        rvalue = llvm_ensure_registers_loaded([rvalue], lvar.pointer_depth - 1)[0]
        rvalue = llvm_int_resize(rvalue, lvar.number_type)

        LLVM_OUT_FILE.writelines(
            [
                TAB,
                "; llvm_store_local",
                NEWLINE,
                TAB,
                f"store {rvalue.llvm_repr}, {lvar.llvm_type} %{lvar.register_name}",
                NEWLINE,
            ]
        )
    elif isinstance(var, SymbolTableEntry) and rvalue.is_register:
        var.latest_llvmvalue = rvalue
    else:
        raise EccoInternalTypeError(
            "SymbolTableEntry", "Nonetype", "llvm.py:llvm_store_local"
        )


def llvm_store_dereference(destination: LLVMValue, value: LLVMValue):
    # If it's a local variable, load it once
    if value.is_likely_local_var:
        value = llvm_ensure_registers_loaded([value], value.pointer_depth - 1)[0]

    destination = llvm_ensure_registers_loaded([destination], value.pointer_depth + 1)[
        0
    ]

    if (
        not destination.just_loaded
        or destination.pointer_depth == value.pointer_depth + 1
    ):
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                "; store_dereference",
                NEWLINE,
                TAB,
                f"store {value.llvm_repr}, {destination.llvm_type} %{destination.register_name}",
                NEWLINE,
            ]
        )
    else:
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                f"store {value.llvm_repr}, {destination.llvm_type}* @{destination.just_loaded}",
                NEWLINE,
            ]
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
                f"%{entry.register.register_name} = alloca {entry.register.llvm_type}, align {entry.align_bytes}",
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
    reg = llvm_ensure_registers_loaded([reg], 0)[0]  # reg.pointer_depth
    reg = llvm_int_resize(reg, NumberType.INT)

    llvm_call_function([reg], "printint")


PURPLE_LABEL_PREFIX: str = "L"


def llvm_label(label: LLVMValue) -> None:
    """Generate a label for branch instructions

    Args:
        label (LLVMValue): LLVMValue containing label index

    Raises:
        EccoInternalTypeError: If a non-label LLVMValue is provided
    """
    if label.value_type != LLVMValueType.LABEL:
        raise EccoInternalTypeError(
            f"{LLVMValueType.LABEL}", f"{label.value_type}", "llvm.py:llvm_label"
        )

    LLVM_OUT_FILE.writelines(
        [NEWLINE, TAB, f"{PURPLE_LABEL_PREFIX}{label.int_value}:", NEWLINE]
    )


def llvm_jump(label: LLVMValue) -> None:
    """Jump to a label unconditionally

    Args:
        label (LLVMValue): LLVMValue containing label index

    Raises:
        EccoInternalTypeError: If a non-label LLVMValue is provided
    """
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
    """Conditionally jump to a label

    Args:
        condition_register (LLVMValue): Register containing condition value
        true_label (LLVMValue): Label to jump to if condition_register = 1
        false_label (LLVMValue): Label to jump to if condition_register = 0

    Raises:
        EccoInternalTypeError: If one of true_label or false_label is not a label
    """
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
            f"br {condition_register.number_type} %{condition_register.register_name}, label %{PURPLE_LABEL_PREFIX}{true_label.int_value}, label %{PURPLE_LABEL_PREFIX}{false_label.int_value}",
            NEWLINE,
        ]
    )


def llvm_compare_jump(
    comparison_type: Token,
    left_vr: LLVMValue,
    right_vr: LLVMValue,
    false_label: LLVMValue,
) -> LLVMValue:
    """Compare and conditionally jump

    Args:
        comparison_type (Token): Type of comparison to perform
        left_vr (LLVMValue): Left operand
        right_vr (LLVMValue): Right operand
        false_label (LLVMValue): Label to jump to if condition_register = 0

    Returns:
        LLVMValue: Result of comparison, i1
    """
    comparison_result: LLVMValue = llvm_comparison(comparison_type, left_vr, right_vr)

    true_label: LLVMValue = get_next_label()

    llvm_conditional_jump(comparison_result, true_label, false_label)

    llvm_label(true_label)

    return comparison_result


def llvm_function_preamble(function_name: str) -> List[LLVMValue]:
    """Generate preamble for a given function

    Args:
        function_name (str): Name of function

    Raises:
        EccoIdentifierError: If function name is undeclared
        EccoInternalTypeError: If provided name does not match a Function type

    Returns:
        LLVMValue: List of LLVMValues containing references to function argument variables
    """
    from .symboltable import SymbolTableEntry

    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            "Tried to generate function preamble for undeclared function"
        )
    elif not isinstance(entry.identifier_type.contents, Function):
        raise EccoInternalTypeError(
            "Function",
            str(entry.identifier_type.type),
            "llvm.py:llvm_function_preamble",
        )

    LLVM_OUT_FILE.writelines(
        [
            f"define dso_local {entry.identifier_type.llvm_repr} @{function_name}(",
            ", ".join(
                [
                    f"{arg_num.llvm_repr} %{get_next_local_virtual_register() - 1}"
                    for arg_num in entry.identifier_type.contents.arguments.values()
                ]
            ),
            # entry.identifier_type.contents.args_llvm_repr,
            ") #0 {",
            NEWLINE,
        ]
    )

    arguments_llvmvalues: List[LLVMValue] = []
    for i, (arg_name, arg_num) in enumerate(
        entry.identifier_type.contents.arguments.items()
    ):
        arguments_llvmvalues.append(
            LLVMValue(
                LLVMValueType.VIRTUAL_REGISTER,
                arg_name,
                arg_num.ntype,
                arg_num.pointer_depth,
                array_type=arg_num if isinstance(arg_num, Array) else None,
                struct_type=arg_num if isinstance(arg_num, Struct) else None,
            )
        )

        # Allocate stack space for the local variable
        llvm_stack_allocation(
            [LLVMStackEntry(arguments_llvmvalues[-1], arg_num.ntype.byte_width)]
        )
        # get_next_local_virtual_register()

        # Store the value passed into the function into the newly alloc'd register
        arguments_llvmvalues[-1].pointer_depth += 1
        llvm_store_local(
            arguments_llvmvalues[-1],
            LLVMValue(
                LLVMValueType.VIRTUAL_REGISTER,
                i,
                arg_num.ntype,
                arg_num.pointer_depth,
                array_type=arg_num if isinstance(arg_num, Array) else None,
                struct_type=arg_num if isinstance(arg_num, Struct) else None,
            ),
        )

        func_arg = SYMBOL_TABLE_STACK.LST[arg_name]
        if not func_arg:
            raise EccoFatalException(
                f"Lost track of parameter '{arg_name}' in function definition '{function_name}'"
            )
        # elif not isinstance(func_arg.identifier_type.contents, Number):
        #     raise EccoFatalException(
        #         f"Tried to use non-number as parameter '{arg_name}' in function definition '{function_name}'"
        #     )

        func_arg.latest_llvmvalue = arguments_llvmvalues[-1]

    return arguments_llvmvalues


def llvm_function_postamble(function_name: str) -> None:
    """Generate postamble for a given function

    Args:
        function_name (str): Name of function

    Raises:
        EccoIdentifierError: If function name is undeclared
        EccoInternalTypeError: If provided name does not match a Function type
    """
    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to close undeclared function "{function_name}"'
        )
    elif not isinstance(entry.identifier_type.contents, Function):
        raise EccoFatalException(
            "",
            f'Tried to close non-function identifier "{function_name}"',
        )

    LLVM_OUT_FILE.writelines([TAB, "ret "])

    if entry.identifier_type.contents.return_type.ntype == NumberType.VOID:
        LLVM_OUT_FILE.write("void" + NEWLINE)
    else:
        LLVM_OUT_FILE.writelines(
            [
                f"{entry.identifier_type.contents.return_type.ntype} 0",
                NEWLINE,
            ]
        )

    LLVM_OUT_FILE.writelines(["}", NEWLINE, NEWLINE])


def llvm_struct_declaration(struct_name: str) -> None:
    entry: Optional[SymbolTableEntry] = SYMBOL_TABLE_STACK.GST[struct_name]
    if not (entry and isinstance(entry.identifier_type.contents, Struct)):
        raise EccoInternalTypeError(
            "Struct", str(type(entry)), "llvm.py:llvm_struct_declaration"
        )

    LLVM_OUT_FILE.writelines([f"%{struct_name} = type {{", NEWLINE])

    for i, (field_name, field_type) in enumerate(
        entry.identifier_type.contents.fields.items()
    ):
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                field_type.llvm_repr,
                "," if i != len(entry.identifier_type.contents.fields) - 1 else "",
                TAB,
                f"; index {i} = {field_name}",
                NEWLINE,
            ]
        )

    LLVM_OUT_FILE.writelines(["}", NEWLINE, NEWLINE])


def llvm_union_declaration(union_name: str) -> None:
    entry: Optional[SymbolTableEntry] = SYMBOL_TABLE_STACK.GST[union_name]
    if not (entry and isinstance(entry.identifier_type.contents, EccoUnion)):
        raise EccoInternalTypeError(
            "Union", str(type(entry)), "llvm.py:llvm_union_declaration"
        )

    max_ntype: Optional[NumberType] = None
    for value in entry.identifier_type.contents.fields.values():
        if not max_ntype or (int(value.ntype) > int(max_ntype)):
            max_ntype = value.ntype
    if not max_ntype:
        return

    LLVM_OUT_FILE.writelines(
        [f"%union.{union_name} = type {{ ", str(max_ntype), " }", NEWLINE, NEWLINE]
    )


def llvm_return(return_value: LLVMValue, function_name: str) -> None:
    """Generatre a return statement

    Args:
        return_value (LLVMValue): Value to return
        function_name (str): Name of function of which to return from

    Raises:
        EccoIdentifierError: If function is undeclared
        EccoFatalException: If provided name does not match a Function type
    """
    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to return for undeclared function "{function_name}"'
        )
    elif not isinstance(entry.identifier_type.contents, Function):
        raise EccoFatalException(
            "",
            f'Tried to generate return statement for non-function identifier "{function_name}"',
        )

    return_value = llvm_ensure_registers_loaded([return_value])[0]
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"ret {return_value.number_type} ",
            f"{return_value.llvm_display_value}"
            if return_value.number_type != NumberType.VOID
            else "",
            NEWLINE,
        ]
    )

    get_next_local_virtual_register()


def llvm_call_function(arguments: List[LLVMValue], function_name: str) -> LLVMValue:
    """Generate function call statement

    Args:
        argument (LLVMValue): (Temporarily unusable) argument to function call
        function_name (str): Name of function to call

    Raises:
        EccoIdentifierError: If function is undeclared
        EccoFatalException: If provided name does not match a Function type

    Returns:
        LLVMValue: Value of evaluated function call
    """
    out: LLVMValue = LLVMValue(LLVMValueType.NONE)

    entry: Optional[SymbolTableEntry] = GLOBAL_SYMBOL_TABLE[function_name]
    if not entry:
        raise EccoIdentifierError(
            f'Tried to generate call for undeclared function "{function_name}"'
        )
    elif not isinstance(entry.identifier_type.contents, Function):
        raise EccoFatalException(
            "",
            f'Tried to call non-function identifier "{function_name}" as function',
        )

    arguments = [
        llvm_int_resize(
            llvm_ensure_registers_loaded([arg], expected_arg.pointer_depth)[0],
            expected_arg.ntype,
        )
        for arg, expected_arg in zip(
            arguments, entry.identifier_type.contents.arguments.values()
        )
    ]

    LLVM_OUT_FILE.write(TAB)

    call_type: str = "void"
    if entry.identifier_type.contents.return_type.ntype != NumberType.VOID:
        out = LLVMValue(
            LLVMValueType.VIRTUAL_REGISTER,
            get_next_local_virtual_register(),
            entry.identifier_type.contents.return_type.ntype,
        )
        LLVM_OUT_FILE.writelines([f"%{out.register_name} = "])
        call_type = str(out.number_type)

    LLVM_OUT_FILE.writelines(
        [
            f"call {call_type} (",
            # Argument types
            ", ".join(
                [
                    value.llvm_repr
                    for value in entry.identifier_type.contents.arguments.values()
                ]
            ),
            f") @{function_name}(",
            # Arguments
            ", ".join(
                [f"{value.llvm_type} {value.llvm_display_value}" for value in arguments]
            ),
            ")",
            NEWLINE,
        ]
    )

    return out


def llvm_get_address(identifier: str) -> LLVMValue:
    """Store the address of an identifier in a virtual register

    Args:
        identifier (str): Variable name to get address of

    Raises:
        EccoFatalException: If variable is undeclared
        EccoInternalTypeError: If provided name does not match Number type

    Returns:
        LLVMValue: LLVMValue containing virtual register containing identifier address
    """
    ste = SYMBOL_TABLE_STACK[identifier]
    if not ste:
        raise EccoIdentifierError(
            f"Undeclared identifier {identifier} was allowed to propagate to LLVM generation",
        )
    elif type(ste.identifier_type.contents) not in [Number, Array]:
        raise EccoInternalTypeError(
            "Number or Array", str(ste.identifier_type.type), "llvm.py:llvm_get_address"
        )

    lv = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        get_next_local_virtual_register(),
        ste.latest_llvmvalue.number_type,
        ste.latest_llvmvalue.pointer_depth,
    )

    lv.pointer_depth -= 1

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{lv.register_name} = getelementptr inbounds {lv.llvm_type}, ",
            f"{ste.latest_llvmvalue.llvm_repr}",
        ]
    )

    LLVM_OUT_FILE.write(NEWLINE)

    lv.pointer_depth += 1

    return lv


def llvm_dereference(value: LLVMValue) -> LLVMValue:
    """Dereference a pointer

    Args:
        value (LLVMValue): Value to dereference

    Returns:
        LLVMValue: Register containing dereferenced contents
    """
    out = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        get_next_local_virtual_register(),
        value.number_type,
        value.pointer_depth - 1,
    )

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out.register_name} = load {out.llvm_type}, {value.llvm_type} %{value.register_name}",
            NEWLINE,
        ]
    )

    return out


def llvm_array_access(array_name: str, offset: LLVMValue) -> LLVMValue:
    ste = SYMBOL_TABLE_STACK[array_name]
    if not ste:
        raise EccoIdentifierError(f'Tried to access non-existent array "{array_name}"')

    if not isinstance(ste.identifier_type.contents, Array):
        # if isinstance(ste.identifier_type.contents, Number) and ste.identifier_type.contents.pointer_depth > 0:

        raise EccoFatalException("", "Non-array stored in array access node")
    arr_type: Array = ste.identifier_type.contents

    offset = llvm_int_resize(offset, NumberType.LONG)

    lv = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        get_next_local_virtual_register(),
        arr_type.ntype,
        arr_type.pointer_depth,
        # array_type=arr_type,
    )

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{lv.register_name} = getelementptr inbounds {ste.latest_llvmvalue.llvm_type[:-1]}, ",
            f"{ste.latest_llvmvalue.llvm_repr}, i64 0, {offset.llvm_repr}",
            NEWLINE,
        ]
    )

    lv.pointer_depth += 1

    # return llvm_dereference(lv)
    return lv


def llvm_struct_access(ident_name: str, struct_name: str, field_name: str) -> LLVMValue:
    ste = SYMBOL_TABLE_STACK[ident_name]
    if not ste:
        raise EccoIdentifierError(f'Lost track of struct object "{ident_name}"')
    if not isinstance(ste.identifier_type.contents, Struct):
        raise EccoInternalTypeError(
            "expression.py:postfix_operator",
            "Struct",
            str(type(ste.identifier_type.contents)),
        )
    struct_obj = ste.identifier_type.contents

    if field_name not in struct_obj.fields:
        raise EccoFatalException(
            "", "Unrecognized field access allowed to progress to code generation"
        )

    field = struct_obj.fields[field_name]
    out = LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        get_next_local_virtual_register(),
        nt=field.ntype if isinstance(field, Number) else NumberType.INT,
        struct_type=field if isinstance(field, Struct) else None,
    )

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out.register_name} = getelementptr %{struct_name}, {ste.latest_llvmvalue.llvm_repr}, i32 0, i32 {list(struct_obj.fields.keys()).index(field_name)}",
            NEWLINE,
        ]
    )

    out.pointer_depth += 1

    return out

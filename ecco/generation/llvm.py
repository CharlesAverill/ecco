from typing import List

from ..scanning import Token, TokenType
from ..utils import EccoFatalException
from .llvmstackentry import LLVMStackEntry
from .llvmvalue import LLVMValue, LLVMValueType
from .translate import (
    LLVM_LOADED_REGISTERS,
    LLVM_OUT_FILE,
    get_next_local_virtual_register,
)

NEWLINE = "\n"
TAB = "\t"


def llvm_preamble():
    LLVM_OUT_FILE.writelines(
        [
            f"; ModuleID = '{LLVM_OUT_FILE.name}'",
            NEWLINE,
            f'source_filename = "{LLVM_OUT_FILE.name}"',
            NEWLINE,
            'target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"',
            NEWLINE,
            'target triple = "x86_64-pc-linux-gnu"',
            NEWLINE,
            NEWLINE,
            '@print_int_fstring = private unnamed_addr constant [4 x i8] c"%d\\0A\\00", align 1',
            NEWLINE,
            NEWLINE,
            "; Function Attrs: noinline nounwind optnone uwtable",
            NEWLINE,
            "define dso_local i32 @main() #0 {",
            NEWLINE,
        ]
    )


def llvm_postamble():
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            "ret i32 0",
            NEWLINE,
            "}",
            NEWLINE,
            NEWLINE,
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
    print("Loaded:", [i.int_value for i in LLVM_LOADED_REGISTERS])
    found_registers: List[bool] = [False] * len(registers_to_check)

    for loaded_register in LLVM_LOADED_REGISTERS:
        for i, reg in enumerate(registers_to_check):
            if reg.int_value == loaded_register.int_value:
                found_registers[i] = True

            if found_registers.count(True) == len(registers_to_check):
                return registers_to_check

    loaded_registers: List[LLVMValue] = []
    for i in range(len(registers_to_check)):
        if not found_registers[i]:
            new_reg = get_next_local_virtual_register()
            loaded_registers.append(LLVMValue(LLVMValueType.VIRTUAL_REGISTER, new_reg))
            LLVM_OUT_FILE.writelines(
                [
                    TAB,
                    f"%{new_reg} = load i32, i32* %{registers_to_check[i].int_value}, align 4",
                    NEWLINE,
                ]
            )
            LLVM_LOADED_REGISTERS.append(loaded_registers[-1])
        else:
            loaded_registers.append(registers_to_check[i])

    return loaded_registers


def llvm_add(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER

    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = add nsw i32 %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr)


def llvm_sub(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER

    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = sub nsw i32 %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr)


def llvm_mul(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER

    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = mul nsw i32 %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr)


def llvm_div(left_vr: LLVMValue, right_vr: LLVMValue) -> LLVMValue:
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER

    out_vr: int = get_next_local_virtual_register()
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"%{out_vr} = udiv i32 %{left_vr.int_value}, %{right_vr.int_value}",
            NEWLINE,
        ]
    )

    return LLVMValue(LLVMValueType.VIRTUAL_REGISTER, out_vr)


def llvm_binary_arithmetic(
    token: Token, left_vr: LLVMValue, right_vr: LLVMValue
) -> LLVMValue:
    out_vr: LLVMValue

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

    LLVM_LOADED_REGISTERS.append(out_vr)

    return out_vr


def llvm_store_constant(value: int) -> LLVMValue:
    global LLVM_OUT_FILE
    from .translate import update_free_register_count

    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"store i32 {value}, i32* %{update_free_register_count(-1)}, align 4",
            NEWLINE,
        ]
    )
    return LLVMValue(
        LLVMValueType.VIRTUAL_REGISTER,
        update_free_register_count(0) + 1,
        True,
    )


def llvm_stack_allocation(entries: List[LLVMStackEntry]):
    global LLVM_OUT_FILE
    for entry in entries:
        LLVM_OUT_FILE.writelines(
            [
                TAB,
                f"%{entry.register.int_value} = alloca i32, align {entry.align_bytes}",
                NEWLINE,
            ]
        )


def llvm_print_int(reg: LLVMValue):
    global LLVM_OUT_FILE
    LLVM_OUT_FILE.writelines(
        [
            TAB,
            f"call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @print_int_fstring , i32 0, i32 0), i32 %{reg.int_value})",
            NEWLINE,
        ]
    )

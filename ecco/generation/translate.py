from typing import List, TextIO

from ..ecco import ARGS
from ..parsing import ASTNode
from ..utils import EccoFileError, LogLevel, log
from .llvmvalue import LLVMValue, LLVMValueType

LLVM_OUT_FILE: TextIO
LLVM_VIRTUAL_REGISTER_NUMBER: int
LLVM_FREE_REGISTER_COUNT: int
LLVM_LOADED_REGISTERS: List[int]


def translate_init():
    global LLVM_OUT_FILE, LLVM_VIRTUAL_REGISTER_NUMBER, LLVM_FREE_REGISTER_COUNT, LLVM_LOADED_REGISTERS

    try:
        LLVM_OUT_FILE = open(ARGS.output, "w")
    except Exception as e:
        raise EccoFileError(str(e))

    LLVM_VIRTUAL_REGISTER_NUMBER = 1

    LLVM_FREE_REGISTER_COUNT = 0

    LLVM_LOADED_REGISTERS = []


def ast_to_llvm(root: ASTNode) -> LLVMValue:
    return LLVMValue(LLVMValueType.LLVMVALUE_NONE, None)


def generate_llvm(root: ASTNode):
    translate_init()

    from .llvm import llvm_postamble, llvm_preamble, llvm_print_int

    llvm_preamble()

    print_vr: LLVMValue = ast_to_llvm(root)

    # llvm_print_int(print_vr.int_value)

    llvm_postamble()

    if not LLVM_OUT_FILE.closed:
        LLVM_OUT_FILE.close()

    log(LogLevel.LOG_DEBUG, f"LLVM written to {LLVM_OUT_FILE.name}")

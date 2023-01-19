from .llvmvalue import LLVMValue


class LLVMStackEntry:
    def __init__(self, register: LLVMValue, align_bytes: int):
        self.register = register
        self.align_bytes = align_bytes

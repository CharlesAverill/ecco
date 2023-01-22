from .llvmvalue import LLVMValue


class LLVMStackEntry:
    def __init__(self, register: LLVMValue, align_bytes: int):
        """Class storing data about the stack requirements of expressions

        Args:
            register (LLVMValue): Register number to assign 'alloca' output to
            align_bytes (int): Bytes to align the 'alloca' statement with,
                               often the byte width of a data type
        """
        self.register = register
        self.align_bytes = align_bytes

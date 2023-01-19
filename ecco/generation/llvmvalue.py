from enum import Enum
from typing import Union

from ..utils.ecco_logging import EccoInternalTypeError


class LLVMValueType(Enum):
    LLVMVALUE_NONE = "LLVMValue (None)"

    LLVMVALUE_VIRTUAL_REGISTER = "LLVMValue (Virtual Register)"

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return LLVMValueType._member_names_.index(self._name_)


class LLVMValue:
    def __init__(
        self, lvt: LLVMValueType, value: Union[int, None], stores_pointer: bool = False
    ):
        self.value_type = lvt
        if lvt == LLVMValueType.LLVMVALUE_VIRTUAL_REGISTER and type(value) != int:
            raise EccoInternalTypeError(
                str(int), str(type(value)), "generation/llvmvalue.py:LLVMValue.__init__"
            )
            self.int_value: int = value

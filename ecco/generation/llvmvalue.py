from enum import Enum
from typing import Union

from ..utils.ecco_logging import EccoInternalTypeError
from .types import NumberType


class LLVMValueType(Enum):
    """An Enum class to store types of LLVMValues"""

    NONE = "None"

    VIRTUAL_REGISTER = "Virtual Register"
    LABEL = "Label"

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return LLVMValueType._member_names_.index(self._name_)


class LLVMValue:
    def __init__(
        self,
        lvt: LLVMValueType,
        value: Union[int, None] = None,
        nt: NumberType = NumberType.INT,
    ):
        """Stores data about various kinds of LLVM Values

        Args:
            lvt (LLVMValueType): The type of LLVMValue to instantiate
            value (Union[int, None]): The stored value\

        Raises:
            EccoInternalTypeError: _description_
        """
        self.value_type: LLVMValueType = lvt
        self.int_value: int = 0
        self.number_type: NumberType = nt

        if self.value_type in [LLVMValueType.VIRTUAL_REGISTER, LLVMValueType.LABEL]:
            if type(value) != int:
                raise EccoInternalTypeError(
                    str(int),
                    str(type(value)),
                    "generation/llvmvalue.py:LLVMValue.__init__",
                )
            self.int_value = value

    def __repr__(self) -> str:
        append: str = ""
        if self.value_type == LLVMValueType.VIRTUAL_REGISTER:
            append = f": %{self.int_value}"
        return f"LLVMValue ({self.value_type} {self.number_type})" + append

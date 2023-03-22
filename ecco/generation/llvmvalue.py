from enum import Enum
from typing import Union

from ..utils.ecco_logging import EccoInternalTypeError
from .types import NumberType


class LLVMValueType(Enum):
    """An Enum class to store types of LLVMValues"""

    NONE = "None"

    VIRTUAL_REGISTER = "Virtual Register"
    LABEL = "Label"
    CONSTANT = "Constant"

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return LLVMValueType._member_names_.index(self._name_)


class LLVMValue:
    def __init__(
        self,
        lvt: LLVMValueType,
        value: Union[int, str, None] = None,
        nt: NumberType = NumberType.INT,
        pointer_depth: int = 0,
        just_loaded: str = "",
    ):
        """Stores data about various kinds of LLVM Values

        Args:
            lvt (LLVMValueType): The type of LLVMValue to instantiate
            value (Union[int, str, None]): The stored value

        Raises:
            EccoInternalTypeError: _description_
        """
        self.value_type: LLVMValueType = lvt
        self.int_value: int = 0
        self.str_value: str = ""
        self.number_type: NumberType = nt
        self.pointer_depth: int = pointer_depth
        self.just_loaded: str = just_loaded

        if self.value_type in [
            LLVMValueType.VIRTUAL_REGISTER,
            LLVMValueType.LABEL,
            LLVMValueType.CONSTANT,
        ]:
            if type(value) == int:
                self.int_value = value
            elif type(value) == str:
                self.str_value = value
            else:
                raise EccoInternalTypeError(
                    "int or str",
                    str(type(value)),
                    "generation/llvmvalue.py:LLVMValue.__init__",
                )

    @property
    def register_name(self) -> str:
        return self.str_value if self.str_value else str(self.int_value)

    @property
    def is_register(self) -> bool:
        return self.value_type == LLVMValueType.VIRTUAL_REGISTER

    @property
    def references(self) -> str:
        return "*" * self.pointer_depth

    def __repr__(self) -> str:
        append: str = ""
        if self.value_type in [LLVMValueType.VIRTUAL_REGISTER, LLVMValueType.CONSTANT]:
            append = f": {'%' if self.value_type == LLVMValueType.VIRTUAL_REGISTER else ''}{self.register_name}"
        if self.just_loaded:
            append += f" (from {self.just_loaded})"
        return (
            f"LLVMValue ({self.value_type} {self.number_type}{self.references})"
            + append
        )

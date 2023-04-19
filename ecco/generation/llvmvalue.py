from enum import Enum
from typing import Union, Optional

from ..utils.ecco_logging import EccoInternalTypeError
from .types import NumberType, Array, Struct


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
        array_type: Optional[Array] = None,
        struct_type: Optional[Struct] = None,
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

        self.is_num: bool = False
        self.array: Optional[Array] = None
        self.struct: Optional[Struct] = None
        if array_type:
            self.array = array_type
            self.array_length: int = array_type.length
        elif struct_type:
            self.struct = struct_type
        else:
            self.is_num = True

        if self.value_type in [
            LLVMValueType.VIRTUAL_REGISTER,
            LLVMValueType.LABEL,
            LLVMValueType.CONSTANT,
        ]:
            if isinstance(value, int):
                self.int_value = value
            elif isinstance(value, str):
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
    def is_likely_local_var(self) -> bool:
        return self.is_register and self.str_value != ""

    @property
    def references(self) -> str:
        return "*" * self.pointer_depth

    @property
    def llvm_type(self) -> str:
        if self.is_num:
            return f"{self.number_type}{self.references}"
        elif self.struct:
            return f"%{self.struct.name}{self.references}"
        else:
            # We are implicitly not supporting arrays of pointers by excluding
            # {something.references} here. We'll need to do a better unification of
            # the LLVMValue and Number classes
            return f"[{self.array_length} x {self.number_type}]{self.references}"

    @property
    def llvm_display_value(self) -> str:
        return f"{'%' if self.is_register else ''}{self.register_name}"

    @property
    def llvm_repr(self) -> str:
        return self.llvm_type + " " + self.llvm_display_value

    def __repr__(self) -> str:
        append: str = ""
        if self.value_type == LLVMValueType.CONSTANT:
            append = f": {self.int_value}"
        if self.just_loaded:
            append += f" (from {self.just_loaded})"
        return f"LLVMValue ({self.llvm_repr})" + append

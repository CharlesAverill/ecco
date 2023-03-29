from enum import Enum
from ..scanning.ecco_token import TokenType
from typing import Union, OrderedDict
from ..utils import EccoInternalTypeError


class NumberType(Enum):
    BOOL = "i1"
    CHAR = "i8"
    SHORT = "i16"
    INT = "i32"
    LONG = "i64"

    VOID = "void"

    @property
    def byte_width(self) -> int:
        if self == NumberType.VOID:
            return 0
        return max(1, int(self.value[1:]) // 4)

    @property
    def max_val(self) -> int:
        if self == NumberType.VOID:
            return 0
        return 2**self.byte_width

    @staticmethod
    def from_int(i) -> "NumberType":
        for t in NumberType:
            if int(t) == i:
                return t
        raise EccoInternalTypeError(
            f"one of {[int(t) for t in NumberType]}",
            str(i),
            "generation/llvm.py:NumberType.from_int",
        )

    @staticmethod
    def from_tokentype(t: TokenType) -> "NumberType":
        if t == TokenType.INT:
            return NumberType.INT
        elif t == TokenType.CHAR:
            return NumberType.CHAR
        elif t == TokenType.VOID:
            return NumberType.VOID

        return NumberType.VOID

    def to_tokentype(self) -> TokenType:
        if self == NumberType.INT:
            return TokenType.INT
        elif self == NumberType.CHAR:
            return TokenType.CHAR
        elif self == NumberType.VOID:
            return TokenType.VOID
        return TokenType.UNKNOWN_TOKEN

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return NumberType._member_names_.index(self._name_)


class Number:
    def __init__(self, ntype: NumberType, value: int, pointer_depth: int = 0):
        self.ntype: NumberType = ntype
        self.value: int = value
        self.pointer_depth = pointer_depth

    @property
    def references(self) -> str:
        return "*" * self.pointer_depth

    @property
    def llvm_repr(self) -> str:
        return f"{self.ntype}{self.references}"


class Function:
    def __init__(self, rtype: Number, arguments: OrderedDict[str, Number]):
        self.return_type: Number = rtype
        self.arguments = arguments

    @property
    def args_llvm_repr(self) -> str:
        return ", ".join(
            f"{self.arguments[argname].llvm_repr} %{argname}"
            for argname in self.arguments.keys()
        )


class Type:
    def __init__(self, ttype: TokenType, value: Union[Number, Function]) -> None:
        self.ttype: TokenType = ttype
        self.contents: Union[Number, Function] = value

    @property
    def type(self):
        return type(self.contents)

    @property
    def llvm_repr(self) -> str:
        if type(self.contents) == Number:
            return str(self.contents.ntype)
        elif type(self.contents) == Function:
            if self.contents.return_type:
                return str(self.contents.return_type.ntype)
            else:
                return "void"
        return "brokentype"

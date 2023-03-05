from enum import Enum
from ..scanning.ecco_token import TokenType
from typing import Union
from ..utils import EccoInternalTypeError


class NumberType(Enum):
    BOOL = "i1"
    CHAR = "i8"
    SHORT = "i16"
    INT = "i32"
    LONG = "i64"

    @property
    def byte_width(self) -> int:
        return max(1, int(self.value[1:]) // 4)

    @property
    def max_val(self) -> int:
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
    def from_tokentype(t: TokenType):
        if t == TokenType.INT:
            return NumberType.INT
        elif t == TokenType.CHAR:
            return NumberType.CHAR
        return None

    def to_tokentype(self):
        if int(self) == int(NumberType.INT):
            return TokenType.INT
        elif int(self) == int(NumberType.CHAR):
            return TokenType.CHAR
        return None

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


class Function:
    def __init__(self, rtype: TokenType):
        self.return_type: TokenType = rtype


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
            if self.contents.return_type == TokenType.VOID:
                return "void"
            return str(NumberType.from_tokentype(self.contents.return_type))
        return "brokentype"

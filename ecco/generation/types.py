from enum import Enum
from ..scanning.ecco_token import TokenType
from typing import Union, OrderedDict
from ..utils import EccoInternalTypeError, EccoArrayError

from typing import List


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
        return max(1, int(self.value[1:]) // 8)

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
        elif t == TokenType.LONG:
            return NumberType.LONG
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

    def __repr__(self) -> str:
        return f"Number [{self.ntype}{'*' * self.pointer_depth}] ({self.value})"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Number):
            return False

        return (
            __value.ntype == self.ntype
            and __value.value == self.value
            and __value.pointer_depth == self.pointer_depth
        )


class Array:
    def __init__(
        self, num: Number, length: int, contents: List[float] = [], dimension: int = 1
    ):
        self.num = num

        # I would like to have this be length <= 0, but C compilers let users
        # define length-0 arrays. That's ridiculous! But I'll stick with the "standard"
        if length < 0:
            raise EccoArrayError("Arrays must have a non-negative length")
        self.length = length

        if not contents:
            contents = [0] * length
        elif len(contents) != length:
            raise EccoArrayError(
                "Length of initializer list does not match declared size"
            )
        self.contents = contents

        if dimension != 1:
            raise EccoArrayError("Only 1D arrays are supported for now!")
        self.dimension = dimension

    @property
    def ntype(self) -> NumberType:
        return self.num.ntype

    @property
    def pointer_depth(self) -> int:
        return self.num.pointer_depth

    @pointer_depth.setter
    def pointer_depth(self, i: int) -> None:
        self.num.pointer_depth = i

    @property
    def llvm_repr(self) -> str:
        return f"[{self.length} x {self.num.llvm_repr}]"


class Function:
    def __init__(
        self,
        rtype: Number,
        arguments: OrderedDict[str, Number],
        is_prototype: bool = False,
    ):
        self.return_type: Number = rtype
        self.arguments = arguments
        self.is_prototype = is_prototype

    @property
    def args_llvm_repr(self) -> str:
        return ", ".join(
            f"{self.arguments[argname].llvm_repr} %{argname}"
            for argname in self.arguments.keys()
        )


class Type:
    def __init__(self, ttype: TokenType, value: Union[Number, Function, Array]) -> None:
        self.ttype: TokenType = ttype
        self.contents: Union[Number, Function, Array] = value

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
        elif type(self.contents) == Array:
            return str(self.contents.ntype)
        return "brokentype"

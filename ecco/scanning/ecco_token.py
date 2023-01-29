from enum import Enum
from typing import List


class TokenType(Enum):
    """An Enum class to store types of Tokens"""

    UNKNOWN_TOKEN = "unknown token"

    EOF = "EOF"

    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"

    # Literals
    INTEGER_LITERAL = "integer literal"

    # Keywords
    PRINT = "print"

    # Miscellaneous
    SEMICOLON = ";"

    @staticmethod
    def from_string(s: str) -> "TokenType":
        for t_type in TokenType:
            if str(t_type) == s:
                return t_type
        return TokenType.UNKNOWN_TOKEN

    @staticmethod
    def string_values() -> List[str]:
        return [str(tt) for tt in TokenType]

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return TokenType._member_names_.index(self._name_)


class Token:
    def __init__(self, _type: TokenType = TokenType.UNKNOWN_TOKEN, _value: int = 0):
        """Stores Token data

        Args:
            _type (TokenType, optional): Type of Token to instantiate. Defaults to TokenType.UNKNOWN_TOKEN.
            _value (int, optional): Value of Token to instantiate. Defaults to 0.
        """
        self.type: TokenType = _type
        self.value: int = _value

    def is_binary_arithmetic(self) -> bool:
        return int(TokenType.PLUS) <= int(self.type) <= int(TokenType.SLASH)

    def is_terminal(self) -> bool:
        return (
            int(TokenType.INTEGER_LITERAL)
            <= int(self.type)
            <= int(TokenType.INTEGER_LITERAL)
        )

    def __repr__(self):
        return f"Token:\n\tTYPE = [{str(self.type)}] ({int(self.type)})" + (
            f"\n\tVALUE = {self.value}"
            if self.type == TokenType.INTEGER_LITERAL
            else ""
        )

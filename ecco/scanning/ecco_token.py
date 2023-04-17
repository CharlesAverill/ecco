from enum import Enum
from typing import List, Union


class TokenType(Enum):
    """An Enum class to store types of Tokens"""

    UNKNOWN_TOKEN = "%unknown token"

    EOF = "%EOF"

    AST_GLUE = "%AST glue"

    # Arithmetic Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"

    # Comparison Operators
    EQ = "=="
    NEQ = "!="
    LT = "<"
    LEQ = "<="
    GT = ">"
    GEQ = ">="

    # Pointers
    DEREFERENCE = "%dereference"
    AMPERSAND = "&"
    ACCESS = "."

    # Literals
    INTEGER_LITERAL = "%integer literal"

    # Types
    VOID = "void"
    INT = "int"
    CHAR = "char"
    LONG = "long"
    STRUCT = "struct"

    # Assignment
    ASSIGN = "="

    # Keywords
    ELSE = "else"
    IF = "if"
    FOR = "for"
    PRINT = "print"
    WHILE = "while"
    RETURN = "return"

    # Miscellaneous
    SEMICOLON = ";"
    IDENTIFIER = "%identifier"
    # LEFTVALUE_IDENTIFIER = "%leftvalue identifier"
    FUNCTION = "%function"
    FUNCTION_CALL = "%function call"
    VAR_DECL = "%variable declaration"
    LEFT_BRACE = "{"
    RIGHT_BRACE = "}"
    LEFT_PARENTHESIS = "("
    RIGHT_PARENTHESIS = ")"
    LEFT_BRACKET = "["
    RIGHT_BRACKET = "]"
    COMMA = ","
    ARRAY_ACCESS = "%array access"

    def is_operator(self):
        return int(TokenType.PLUS) <= int(self) <= int(TokenType.SLASH)

    def is_type(self):
        return int(TokenType.VOID) <= int(self) <= int(TokenType.STRUCT)

    def is_literal(self):
        return (
            int(TokenType.INTEGER_LITERAL)
            <= int(self)
            <= int(TokenType.INTEGER_LITERAL)
        )

    @staticmethod
    def from_string(c: str, next_char: str) -> "TokenType":
        # This is a temporary tactic we'll use to check length-2 tokens that
        # collide with other tokens, like == and =. This only works with
        # tokens that start with non-identifier characters. When we add
        # if and for etc., we'll have to think of something smarter
        shortcircuit_token = None
        if c == "=" and next_char == "=":
            shortcircuit_token = TokenType.EQ
        elif c == "!" and next_char == "=":
            shortcircuit_token = TokenType.NEQ
        elif c == "<" and next_char == "=":
            shortcircuit_token = TokenType.LEQ
        elif c == ">" and next_char == "=":
            shortcircuit_token = TokenType.GEQ

        if not shortcircuit_token:
            if next_char:
                from ..ecco import GLOBAL_SCANNER

                GLOBAL_SCANNER.put_back(next_char)
        else:
            return shortcircuit_token

        # Regular single-length token checking
        for t_type in TokenType:
            if str(t_type) == c:
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
    def __init__(
        self,
        _type: TokenType = TokenType.UNKNOWN_TOKEN,
        _values: Union[int, str, List[Union[int, str]]] = [0],
    ):
        """Stores Token data

        Args:
            _type (TokenType, optional): Type of Token to instantiate. Defaults to TokenType.UNKNOWN_TOKEN.
            _value (int, optional): Value of Token to instantiate. Defaults to 0.
        """
        self.type: TokenType = _type

        # Getting around the linter
        def to_list(x):
            if not isinstance(x, list):
                return [x]
            return x

        self.values = to_list(_values)

    def is_binary_arithmetic(self) -> bool:
        return int(TokenType.PLUS) <= int(self.type) <= int(TokenType.SLASH)

    def is_comparison_operator(self) -> bool:
        return int(TokenType.EQ) <= int(self.type) <= int(TokenType.GEQ)

    def is_terminal(self) -> bool:
        return (
            int(TokenType.INTEGER_LITERAL)
            <= int(self.type)
            <= int(TokenType.INTEGER_LITERAL)
        )

    @property
    def value(self) -> Union[int, str]:
        return self.values[0]

    @value.setter
    def value(self, v: Union[int, str]) -> None:
        self.values[0] = v

    def __repr__(self):
        return f"Token:\n\tTYPE = [{str(self.type)}] ({int(self.type)})" + (
            f"\n\tVALUE = {self.value}"
            if self.type
            in [
                TokenType.INTEGER_LITERAL,
                TokenType.IDENTIFIER,
            ]
            else ""
        )

import os
from typing import Annotated, List, TextIO

from ..utils.ecco_logging import EccoFileNotFound, EccoSyntaxError
from .ecco_token import Token, TokenType


class Scanner:
    def __init__(self, input_fn: str):
        """A class for scanning in Tokens

        Args:
            input_fn (str): Filename of the input program file
        """
        self.filename: str = input_fn
        self.file: TextIO

        self.put_back_buffer: Annotated[str, 1] = ""

        self.line_number: int = 1

        self.current_token: Token

        self.initialized: bool = False

    # def __enter__(self: Scanner): -> Scanner:
    def __enter__(self):
        """Opens the program file for scanning

        Raises:
            EccoFileNotFound: If the program file does not exist
        """
        if os.path.exists(self.filename):
            self.file = open(self.filename, "r")
        else:
            raise EccoFileNotFound(self.filename)

        self.initialized = True

        return self

    def __exit__(self, _, __, ___):
        """Closes the program file"""
        self.file.close()

    def open(self):
        self.__enter__()

    def close(self):
        self.__exit__(None, None, None)

    def next_character(self) -> Annotated[str, 1]:
        """Get the next character from the input stream

        Returns:
            Annotated[str, 1]: The next character from the input stream
        """
        c: Annotated[str, 1] = ""

        # If we have a character in the putback buffer,
        # we want to read that first, then empty the
        # buffer
        if self.put_back_buffer:
            c = self.put_back_buffer
            self.put_back_buffer = ""
            return c

        # Otherwise, we read a single character from
        # the open input file, and conditionally
        # increment our rudimentary line counter
        c = self.file.read(1)
        if c == "\n":
            self.line_number += 1

        return c

    def skip(self) -> Annotated[str, 1]:
        """Gets the next non-whitespace character from the input stream

        Returns:
            Annotated[str, 1]: The next non-whitespace character from the input stream
        """
        c: Annotated[str, 1] = self.next_character()
        while c.isspace():
            c = self.next_character()
        return c

    def put_back(self, c: Annotated[str, 1]) -> None:
        """Put a character back into the input stream

        Args:
            c (Annotated[str, 1]): Character to put back into the input stream
        """
        if len(c) != 1:
            raise TypeError(
                f"put_back() expected a character, but string of length {len(c)} found"
            )

        self.put_back_buffer = c

    def scan_integer_literal(self, c: Annotated[str, 1]) -> int:
        """Scan integer literals into a buffer and parse them into int objects

        Args:
            c (Annotated[str, 1]): Current character from input stream

        Returns:
            int: Scanned integer literal
        """
        in_string: str = ""

        while c.isdigit():
            in_string += c
            c = self.next_character()

        self.put_back(c)

        return int(in_string)

    def scan(self) -> Token:
        """Scan the next token

        Raises:
            EccoSyntaxError: If an unrecognized Token is reached

        Returns:
            Token: A Token object with the latest scanned data, or None if EOF is reached
        """
        c: Annotated[str, 1] = self.skip()
        self.current_token = Token()

        # Check for EOF
        if c == "":
            self.current_token.type = TokenType.EOF
            return self.current_token

        possible_token_types: List[TokenType] = []
        for token_type in TokenType:
            if str(token_type)[0] == c:
                possible_token_types.append(token_type)

        if not len(possible_token_types):
            if c.isdigit():
                self.current_token.type = TokenType.INTEGER_LITERAL
                self.current_token.value = self.scan_integer_literal(c)
            else:
                raise EccoSyntaxError(f'Uncrecognized token "{c}"')
        else:
            if len(c) == 1:
                self.current_token.type = possible_token_types[0]
                return self.current_token
            else:
                pass

        return self.current_token

    def scan_file(self) -> None:
        """Scans a file and prints out its Tokens"""
        token: Token = Token()

        while self.scan(token):
            print(token)

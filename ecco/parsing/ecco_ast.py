from ..scanning import Token
from copy import deepcopy
from typing import Optional

from ..generation.types import NumberType


class ASTNode:

    function_return_type: Optional[NumberType] = None

    def __init__(
        self,
        from_token: Token,
        left: Optional["ASTNode"] = None,
        middle: Optional["ASTNode"] = None,
        right: Optional["ASTNode"] = None,
    ):
        """A class for storing Abstract Syntax Tree data

        Args:
            from_token (Token): Token corresponding to this AST Node
            left (Optional["ASTNode"], optional): Left child. Defaults to None.
            left (Optional["ASTNode"], optional): Middle child. Defaults to None.
            right (Optional["ASTNode"], optional): Right child. Defaults to None.
        """
        self.token: Token = deepcopy(from_token)

        self.left = left
        if self.left:
            self.left.parent = self

        self.middle = middle
        if self.middle:
            self.middle.parent = self

        self.right = right
        if self.right:
            self.right.parent = self

        self.parent: ASTNode

    @property
    def type(self):
        return self.token.type

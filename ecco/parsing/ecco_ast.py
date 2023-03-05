from ..scanning import Token, TokenType
from copy import deepcopy
from typing import Optional, List
from ..generation.types import Number, NumberType


class ASTNode:
    def __init__(
        self,
        from_token: Token,
        left: Optional["ASTNode"] = None,
        middle: Optional["ASTNode"] = None,
        right: Optional["ASTNode"] = None,
        tree_type: Number = Number(NumberType.INT, 0),
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

        self.tree_type: Number = tree_type

    @property
    def type(self) -> TokenType:
        return self.token.type

    @property
    def children(self) -> List["Optional[ASTNode]"]:
        return [self.left, self.middle, self.right]

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ASTNode):
            return False

        if self.children:
            return (
                self.left == o.left
                and self.middle == o.middle
                and self.right == o.right
            )

        return self.type == o.type and self.token.value == o.token.value

    def __str__(self):
        out = "ASTNode:\n"
        out += f"\tData: {self.token.type} {str(self.token.value)}\n"
        if self.left:
            out += f"\tLeft: {self.left.token.type} {str(self.left.token.value)}\n"
        if self.middle:
            out += (
                f"\tMiddle: {self.middle.token.type} {str(self.middle.token.value)}\n"
            )
        if self.right:
            out += f"\tRight: {self.right.token.type} {str(self.right.token.value)}\n"

        return out

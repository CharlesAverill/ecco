from ..scanning import Token, TokenType
from copy import deepcopy
from typing import Optional, List, Union
from ..generation.types import Number, NumberType, Array, Struct, EccoUnion


class ASTNode:
    def __init__(
        self,
        from_token: Token,
        left: Optional["ASTNode"] = None,
        middle: Optional["ASTNode"] = None,
        right: Optional["ASTNode"] = None,
        tree_type: Union[Array, Number, Struct, EccoUnion] = Number(NumberType.INT, 0),
        function_call_arguments: List["ASTNode"] = [],
    ):
        """A class for storing Abstract Syntax Tree data

        Args:
            from_token (Token): Token corresponding to this AST Node
            left (Optional["ASTNode"], optional): Left child. Defaults to None.
            left (Optional["ASTNode"], optional): Middle child. Defaults to None.
            right (Optional["ASTNode"], optional): Right child. Defaults to None.
            tree_type (Number): Number containing tree number data
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

        self._is_rvalue: Optional[bool] = None
        # self.is_rvalue = is_rvalue

        self.function_call_arguments = function_call_arguments

        self.parent: ASTNode

        self.tree_type = tree_type

    @property
    def is_rvalue(self) -> bool:
        return self._is_rvalue if isinstance(self._is_rvalue, bool) else False

    @is_rvalue.setter
    def is_rvalue(self, b: bool) -> None:
        self._is_rvalue = b
        # for child in [self.left, self.middle, self.right]:
        #     if child and child._is_rvalue is None:
        #         child.is_rvalue = b

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
        out = f"ASTNode{' (rvalue)' if self.is_rvalue else ''}:\n"
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

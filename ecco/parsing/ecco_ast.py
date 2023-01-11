from ..scanning import Token
from copy import deepcopy
from typing import Union


class ASTNode:
    def __init__(
        self,
        from_token: Token,
        left: Union["ASTNode", None] = None,
        right: Union["ASTNode", None] = None,
    ):
        """A class for storing Abstract Syntax Tree data

        Args:
            from_token (Token): Token corresponding to this AST Node
            left (Union['ASTNode', None], optional): Left child. Defaults to None.
            right (Union['ASTNode', None], optional): Right child. Defaults to None.
        """
        self.token: Token = deepcopy(from_token)

        self.left = left
        if self.left:
            self.left.parent = self
        self.right = right
        if self.right:
            self.right.parent = self

        self.parent: ASTNode


def create_ast_leaf(from_token: Token) -> ASTNode:
    """Create an AST leaf Node (no children)

    Args:
        from_token (Token): Token corresponding to this AST Node

    Returns:
        ASTNode: ASTNode encoding the information of the passed token
    """
    return ASTNode(from_token, None, None)


def create_unary_ast_node(from_token: Token, child: ASTNode) -> ASTNode:
    """Create an AST leaf Node (one child)

    Args:
        from_token (Token): Token corresponding to this AST Node

    Returns:
        ASTNode: ASTNode encoding the information of the passed token
    """
    return ASTNode(from_token, child, None)

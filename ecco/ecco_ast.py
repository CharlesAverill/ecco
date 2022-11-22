from .scanning import Token
from copy import deepcopy


class ASTNode:
    def __init__(self, from_token: Token, left=None, right=None):
        self.token: Token = deepcopy(from_token)

        self.left = left
        if self.left:
            self.left.parent = self
        self.right = right
        if self.right:
            self.right.parent = self

        self.parent = None


def create_ast_leaf(from_token: Token) -> ASTNode:
    return ASTNode(from_token, None, None)


def create_unary_ast_node(from_token: Token, child: ASTNode) -> ASTNode:
    return ASTNode(from_token, child, None)

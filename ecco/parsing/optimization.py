from .ecco_ast import ASTNode
from ..scanning import TokenType, Token
from typing import Optional
from copy import deepcopy


def is_const(root: Optional[ASTNode]) -> bool:
    return (root is not None) and root.type.is_literal()


def zero_opt(root: ASTNode) -> ASTNode:
    """Apply AST optimizations when one child is a 0 constant, such as
    x + 0 = x, commutative
    x - 0 = x
    0 - x = -x
    x * 0 = 0, commutative
    0 / x = 0
    x / 0 = Error

    Args:
        root (ASTNode): ASTNode to optimize

    Raises:
        ZeroDivisionError: If a division by zero is detected

    Returns:
        ASTNode: ASTNode, possibly optimized
    """
    from ..ecco import GLOBAL_SCANNER

    zero_ast_node = ASTNode(Token(TokenType.INTEGER_LITERAL, 0))

    # Determine which of the children is nonzero
    nonzero_child: ASTNode = zero_ast_node
    if root.left and root.right:
        if is_const(root.right) and root.right.token.value == 0:
            nonzero_child = root.left
        elif is_const(root.left) and root.left.token.value == 0:
            nonzero_child = root.right
    if nonzero_child == zero_ast_node:
        return root

    # x + 0 = x, commutative
    if root.type == TokenType.PLUS:
        return nonzero_child
    # x - 0 = x
    # 0 - x = -x
    elif root.type == TokenType.MINUS and is_const(root.left) and is_const(root.right):
        if root.left == nonzero_child:
            return root.left
        else:
            if root.left:
                root.left.token.value *= -1
                return root.left
            # Never happens, appease linter
            return root
    # x * 0 = 0, commutative
    elif root.type == TokenType.STAR:
        return zero_ast_node
    # 0 / x = 0
    # x / 0 -> DivideByZeroError
    elif root.type == TokenType.SLASH:
        if root.right == nonzero_child:
            return zero_ast_node
        raise ZeroDivisionError(f"Divide by Zero on L{GLOBAL_SCANNER.line_number}")

    return root


def two_const(root: ASTNode) -> ASTNode:
    """Apply AST optimizations when both children are constants and the operation
       is a binary operation

    Args:
        root (ASTNode): ASTNode to optimize

    Returns:
        ASTNode: ASTNode, possibly optimized
    """
    if not (is_const(root.left) and is_const(root.right)):
        return root

    value: int
    if root.type == TokenType.PLUS and root.left and root.right:
        value = int(root.left.token.value) + int(root.right.token.value)
    elif root.type == TokenType.MINUS and root.left and root.right:
        value = int(root.left.token.value) - int(root.right.token.value)
    elif root.type == TokenType.STAR and root.left and root.right:
        value = int(root.left.token.value) * int(root.right.token.value)
    elif root.type == TokenType.SLASH and root.left and root.right:
        value = int(root.left.token.value) // int(root.right.token.value)
    else:
        return root

    return ASTNode(Token(TokenType.INTEGER_LITERAL, value))


def double_op(root: ASTNode) -> ASTNode:
    """Apply AST optimizations when nested, repeated operations exist, such as
    x + y + z = (x + y) + z
    x * y * z = (x * y) * z
    # x - y - z = x - (y + z)
    # x / y / z = x / (y * z)

    Args:
        root (ASTNode): _description_

    Returns:
        ASTNode: _description_
    """
    target: ASTNode
    nontarget: ASTNode
    if root.left and root.right:
        if root.type == root.left.type:
            target = root.left
            nontarget = root.right
        elif root.type == root.right.type:
            target = root.right
            nontarget = root.left
        else:
            return root
    else:
        return root

    # x + y + z = (x + y) + z
    # x * y * z = (x * y) * z
    if root.type in [TokenType.PLUS, TokenType.STAR]:
        optimized_left = optimize_AST(
            ASTNode(Token(root.type), nontarget, None, target.left)
        )

        return ASTNode(Token(root.type), optimized_left, None, target.right)
    # x - y - z = x - (y + z)
    # x / y / z = x / (y * z)
    elif root.type in [TokenType.MINUS, TokenType.SLASH]:
        optimized_right = optimize_AST(
            ASTNode(
                Token(
                    TokenType.PLUS if root.type == TokenType.MINUS else TokenType.STAR
                ),
                nontarget,
                None,
                target.right,
            )
        )

        return ASTNode(Token(root.type), target.left, None, optimized_right)

    return root


def optimize_AST(root: ASTNode) -> ASTNode:
    """Optimize an AST

    Args:
        root (ASTNode): ASTNode to optimize

    Returns:
        ASTNode: ASTNode, possibly optimized
    """
    from ..ecco import ARGS

    if ARGS.opt == 0 or not root:
        return root

    # before_opt will be used to check if an optimization did anything
    before_opt = deepcopy(root)
    # opt_pass will be our in-progress optimized ASTNode
    opt_pass = deepcopy(before_opt)

    # Do recursive descent immediately, we want to start with leave nodes
    if opt_pass.left:
        opt_pass.left = optimize_AST(opt_pass.left)
    elif opt_pass.middle:
        opt_pass.middle = optimize_AST(opt_pass.middle)
    elif opt_pass.right:
        opt_pass.right = optimize_AST(opt_pass.right)

    # As long as we have children, and as long as our optimizations change
    # the AST, continue optimizing
    while root.children:
        before_opt = deepcopy(opt_pass)

        opt_pass = two_const(opt_pass)
        opt_pass = zero_opt(opt_pass)
        opt_pass = double_op(opt_pass)

        # Our optimizations haven't done anything, so break
        if opt_pass == before_opt or ARGS.opt == 1:
            break

    return before_opt

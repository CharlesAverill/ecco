from .scanning import Scanner, TokenType

from .utils import get_args, setup_tracebacks, EccoFatalException

DEBUG = True
GLOBAL_SCANNER: Scanner = None


def main():
    """Entrypoint for the compiler"""
    global GLOBAL_SCANNER
    args = get_args()

    GLOBAL_SCANNER = Scanner(args.PROGRAM)
    GLOBAL_SCANNER.open()

    setup_tracebacks()
    GLOBAL_SCANNER.scan()
    from .parsing import parse_binary_expression

    parsed_ast = parse_binary_expression()

    def interpret_ast(root):
        left_value: int
        right_value: int

        if root.left:
            left_value = interpret_ast(root.left)
        if root.right:
            right_value = interpret_ast(root.right)

        if root.token.type == TokenType.PLUS:
            return left_value + right_value
        elif root.token.type == TokenType.MINUS:
            return left_value - right_value
        elif root.token.type == TokenType.STAR:
            return left_value * right_value
        elif root.token.type == TokenType.SLASH:
            return left_value // right_value
        elif root.token.type == TokenType.INTEGER_LITERAL:
            return root.token.value
        else:
            raise EccoFatalException(
                "FATAL", f'Unknown Token "{str(root.token.type)}" encountered'
            )

    print(interpret_ast(parsed_ast))

    GLOBAL_SCANNER.close()


if __name__ == "__main__":
    main()

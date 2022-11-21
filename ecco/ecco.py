from .scanning import Scanner
from .utils import get_args, setup_tracebacks

DEBUG = True


def main():
    """Entrypoint for the compiler"""
    args = get_args()

    with Scanner(args.PROGRAM) as scanner:
        setup_tracebacks()
        scanner.scan_file()


if __name__ == "__main__":
    main()

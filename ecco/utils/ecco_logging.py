import sys

ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[38:5:196m"
ANSI_ORANGE = "\033[38:5:208m"
ANSI_YELLOW = "\033[38:5:178m"
ANSI_RESET = "\033[0m"

ERROR_RED = ANSI_RED + ANSI_BOLD
ERROR_ORANGE = ANSI_ORANGE + ANSI_BOLD
ERROR_YELLOW = ANSI_YELLOW + ANSI_BOLD


def setup_tracebacks() -> None:
    from ..ecco import DEBUG

    if not DEBUG:
        sys.tracebacklimit = 0


class EccoFatalException(Exception):
    return_code = 1

    def __init__(self, category_string: str = "FATAL", *args):
        """Generic fatal exception

        Args:
            category_string (str): String describing what kind of fatal error occurred
            *args: Values to be concatenated to the error message, space-separated
        """
        self.message = f"{ERROR_RED}[{category_string}]{ANSI_RESET}"
        if args:
            self.message += " - " + " ".join(args)

        """
        This is bad lol don't do this normally,
        we just don't want to expose compiler implementation
        details to users, and the default exception
        class will print out the full import path
        of whatever exception is called. Also, spitting
        out custom return codes (not supported by exceptions)
        is really useful for people writing scripts
        that use the compiler
        """
        print(self.message)
        sys.exit(self.return_code)

        # super().__init__(self.message)


class EccoFileNotFound(EccoFatalException):
    return_code = 2

    def __init__(self, filename: str):
        """An exception to be thrown when an expected file does not exist

        Args:
            filename (str): Name of file not found
        """
        super().__init__("FILE ERROR", f'File "{filename}" not found')


class EccoSyntaxError(EccoFatalException):
    return_code = 3

    def __init__(self, message: str):
        """An exception to be thrown when a syntax error is encountered

        Args:
            message (str): Message to print after error type
        """
        super().__init__("SYNTAX ERROR", message)

import sys
from enum import Enum

ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[38:5:196m"
ANSI_ORANGE = "\033[38:5:208m"
ANSI_YELLOW = "\033[38:5:178m"
ANSI_RESET = "\033[0m"

ERROR_RED = ANSI_RED + ANSI_BOLD
ERROR_ORANGE = ANSI_ORANGE + ANSI_BOLD
ERROR_YELLOW = ANSI_YELLOW + ANSI_BOLD


class LogLevel(Enum):
    NONE = ("", ANSI_RESET)
    DEBUG = ("[DEBUG]", ANSI_BOLD)
    INFO = ("[INFO]", ANSI_BOLD)
    WARNING = ("[WARNING]", ANSI_YELLOW)
    ERROR = ("[ERROR]", ANSI_RED)
    CRITICAL = ("[CRITICAL]", ANSI_RED)

    def ansi(self) -> str:
        return self._value_[1]

    def __str__(self) -> str:
        return self._value_[0]

    def __int__(self) -> int:
        return LogLevel._member_names_.index(self._name_)


STRING_TO_LEVEL = {
    "NONE": LogLevel.NONE,
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
    "CRITICAL": LogLevel.CRITICAL,
}


def setup_tracebacks() -> None:
    from ..ecco import ARGS

    if not ARGS.logging == "DEBUG":
        sys.tracebacklimit = 0


def log(level: LogLevel, message: str, override_category_str: str = ""):
    from ..ecco import ARGS

    if ARGS.logging == "NONE":
        return

    category_str = override_category_str if override_category_str != "" else str(level)

    if int(level) >= int(STRING_TO_LEVEL[ARGS.logging]):
        print(f"{level.ansi()}{category_str}: {message}{ANSI_RESET}")


class EccoFatalException(Exception):
    return_code = 1

    def __init__(self, category_string: str = "", *args):
        from ..ecco import GLOBAL_SCANNER, ARGS

        """Generic fatal exception

        Args:
            category_string (str): String describing what kind of fatal error occurred
            *args: Values to be concatenated to the error message, space-separated
        """
        message = " - " + " ".join(args) if args else ""

        error_header = f'File "{ARGS.PROGRAM}", line {GLOBAL_SCANNER.line_number}:{GLOBAL_SCANNER.char_number}\n'

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
        log(LogLevel.ERROR, error_header + message, category_string)
        sys.exit(self.return_code)

        # super().__init__(self.message)


class EccoNonfatalWarning(Warning):
    def __init__(self, *args):
        message = ""

        if args:
            message = " ".join(args)

        log(LogLevel.WARNING, message)


class EccoFileNotFound(EccoFatalException):
    return_code = 2

    def __init__(self, filename: str):
        """An exception to be thrown when an expected file does not exist

        Args:
            filename (str): Name of file not found
        """
        super().__init__("FILE ERROR", f'File "{filename}" not found')


class EccoFileError(EccoFatalException):
    return_code = 3

    def __init__(self, message: str):
        """An exception to be thrown when a general File I/O error occurs

        Args:
            message (str): Message to display
        """
        super().__init__("FILE ERROR", message)


class EccoSyntaxError(EccoFatalException):
    return_code = 4

    def __init__(self, message: str):
        """An exception to be thrown when a syntax error is encountered

        Args:
            message (str): Message to print after error type
        """
        super().__init__("SYNTAX ERROR", message)


class EccoInternalTypeError(EccoFatalException):
    return_code = 5

    def __init__(self, expected_type: str, received_type: str, file_function: str):
        """An error to be thrown when type mismatching has occurred in the
        compiler backend

        Args:
            expected_type (str): Expected type of an object
            received_type (str): Actual type of the object
            file_function (str): The file and function in which the mismatch
                                 occurred
        """
        super().__init__(
            "INTERNAL TYPE ERROR",
            "Expected",
            expected_type,
            "but got",
            received_type,
            "in",
            file_function,
        )


class EccoIdentifierError(EccoFatalException):
    return_code = 6

    def __init__(self, message: str):
        """An error to be thrown when an issue with an identifier is encountered

        Args:
            message (str): Message to print after error type
        """
        super().__init__("IDENTIFIER ERROR", message)


class EccoEOFMissingSemicolonError(EccoFatalException):
    return_code = 7

    def __init__(self):
        super().__init__(
            "SYNTAX ERROR", "Encountered unexpected EOF, did you forget a semicolon?"
        )


class EccoArrayError(EccoFatalException):
    return_code = 8

    def __init__(self, message: str):
        super().__init__("ARRAY ERROR", message)

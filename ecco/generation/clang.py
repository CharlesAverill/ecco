from .translate import LLVM_GLOBALS_FILE, LLVM_OUT_FILE
from .llvm import LLVM_GLOBALS_PLACEHOLDER
from tempfile import TemporaryFile
from typing import IO


def link_llvm_globals() -> None:
    LLVM_OUT_FILE.seek(0)
    LLVM_GLOBALS_FILE.seek(0)
    temp: IO[str] = TemporaryFile(mode="w+")

    for line in LLVM_OUT_FILE:
        # Check if current line is placeholder
        if LLVM_GLOBALS_PLACEHOLDER in line:
            # Copy entire globals file into temp file
            temp.writelines(LLVM_GLOBALS_FILE.readlines())
        else:
            temp.write(line)

    LLVM_OUT_FILE.seek(0)
    LLVM_OUT_FILE.truncate(0)
    temp.seek(0)

    LLVM_OUT_FILE.writelines(temp.readlines())

    temp.close()

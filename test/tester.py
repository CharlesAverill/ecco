import subprocess
from pathlib import Path
import os

def _tester(test_name: str, expected: str):
    examples_dir = Path(__file__).parents[1] / "examples"
    subprocess.call(["poetry", "run", "ecco", f"{examples_dir}/{test_name}"])
    subprocess.call(["clang", f"{test_name}.ll"])
    actual: str = subprocess.check_output(["./a.out"]).decode()
    
    actual_lines = actual.splitlines()
    while len(actual_lines) and "SetuptoolsDeprecationWarning" in actual_lines[0]:
        actual_lines = actual_lines[1:]

    assert expected.strip() == actual.strip()

    os.remove(f"{test_name}.ll")
    os.remove("a.out")

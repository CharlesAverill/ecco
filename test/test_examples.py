from .tester import _tester
from .generate_arithmetic_test import generate_arithmetic_test


def test_condition():
    _tester("test_condition", "6")


def test_variables():
    _tester("test_variables", "17")


def test_variable_reassignment():
    _tester(
        "test_variable_reassignment",
        """1
2
3
4
5""",
    )


def test_comparison_operators():
    _tester(
        "test_comparison_operators",
        """1
1
1
1
1
1
1
1
1""",
    )


def test_while_loop():
    _tester(
        "test_while_loop",
        """1
2
3
4
5
6
7
8
9
10""",
    )


def test_for_loop():
    _tester(
        "test_for_loop",
        """1
2
3
4
5
6
7
8
9
10""",
    )


def test_function():
    _tester(
        "test_function",
        """6
6
7
6
7
42
162""",
    )


def test_factorial():
    _tester("test_factorial", """120
120""")


def test_pointers():
    _tester(
        "test_pointers",
        """18
18
12
12
5""",
    )


def test_dereference_assignment():
    _tester("test_dereference_assignment", """3
3
3
5
50""")


def test_empty_prog():
    _tester("test_empty_prog", "")


def test_arithmetic():
    _tester("test_arithmetic", generate_arithmetic_test(500))

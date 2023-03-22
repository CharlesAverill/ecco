from .tester import _tester
from .generate_arithmetic_test import generate_arithmetic_test


def test1():
    _tester("test1", "6")


def test2():
    _tester("test2", "17")


def test3():
    _tester(
        "test3",
        """1
2
3
4
5""",
    )


def test4():
    _tester(
        "test4",
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


def test5():
    _tester(
        "test5",
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


def test6():
    _tester(
        "test6",
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


def test7():
    _tester(
        "test7",
        """6
5
5
35""",
    )


def test8():
    _tester("test8", "7")


def testfactorial():
    _tester("factorial", "120")


def test9():
    _tester(
        "test9",
        """18
18
12
12
5""",
    )


def testopt():
    _tester("opt_test", """3
3
3
-3
0
0
0
10
120
5
17
340
8
50""")


def test10():
    _tester("test10", """3
3
3
5
50""")


def test_arithmetic():
    _tester("arith_test", generate_arithmetic_test(500))


def test_empty():
    _tester("empty", "")

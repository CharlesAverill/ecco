from .tester import _tester

def test1():
    _tester("test1", "6")

def test2():
    _tester("test2", "17")

def test3():
    _tester("test3", """1
2
3
4
5""")

def test4():
    _tester("test4", """1
1
1
1
1
1
1
1
1""")

def test5():
    _tester("test5", """1
2
3
4
5
6
7
8
9
10""")


def test6():
    _tester("test6", """1
2
3
4
5
6
7
8
9
10""")


def test7():
    _tester("test7", """6
5
5
35""")


def test8():
    _tester("test8", "7")


def factorial():
    _tester("factorial", "120")

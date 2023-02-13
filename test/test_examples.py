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

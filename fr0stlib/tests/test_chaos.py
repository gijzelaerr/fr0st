from unittest import TestCase
import operator
from fr0stlib import Chaos


class FakeXform(object):
    def __init__(self, is_final):
        self.final = is_final

    def isfinal(self):
        return self.final

    @property
    def _parent(self):
        class Temp(object):
            pass

        parent = Temp()
        parent.xform = [self]
        return parent
    

class TestChaos(TestCase):
    def setUp(self):
        self.chaos = Chaos(FakeXform(False), [1.0])
        self.final_chaos = Chaos(FakeXform(True), [1.0])

    def test_len(self):
        self.assertEquals(len(self.chaos), 1)
        self.assertEquals(len(self.final_chaos), 0)

    def test_iter(self):
        self.assertEquals(list(self.chaos), [1.0])
        self.assertEquals(list(self.final_chaos), [])

    def test_getitem(self):
        self.assertEquals(self.chaos[0], 1.0)
        self.assertEquals(self.chaos[-1], 1.0)

        self.assertRaises(IndexError, 
                lambda: operator.getitem(self.chaos, 1))

        self.assertRaises(IndexError, 
                lambda: operator.getitem(self.chaos, -2))

        self.assertRaises(IndexError, 
                lambda: operator.getitem(self.final_chaos, 0))

        self.assertRaises(IndexError, 
                lambda: operator.getitem(self.final_chaos, -1))

    def test_getslice(self):
        self.assertEquals(self.chaos[0:], [1.0])
        self.assertEquals(self.chaos[:], [1.0])

    def test_setitem(self):
        self.assertEquals(len(self.chaos), 1)

        self.chaos[0] = 2.0
        self.assertEquals(self.chaos[0], 2.0)
        self.chaos[-1] = 3.0
        self.assertEquals(self.chaos[-1], 3.0)
        self.assertEquals(self.chaos[0], 3.0)
        self.chaos[0] = 1.0

        self.assertRaises(ValueError,
                lambda: operator.setitem(self.chaos, 0, -1))

        self.assertRaises(IndexError, 
                lambda: operator.setitem(self.chaos, 1, 0))

        self.assertRaises(IndexError, 
                lambda: operator.setitem(self.chaos, -2, 0))

    def test_setslice(self):
        self.assertEquals(self.chaos[0], 1.0)

        self.chaos[:] = [2.0]
        self.assertEquals(self.chaos[0], 2.0)
        self.assertEquals(len(self.chaos), 1)

        self.chaos[0:] = [3.0]
        self.assertEquals(self.chaos[0], 3.0)
        self.assertEquals(len(self.chaos), 1)


    def test_to_string(self):
        self.assertEquals(self.chaos.to_string(), '')

        s = 'chaos="%s " ' % 2.0
        self.chaos[0] = 2.0
        self.assertEquals(self.chaos.to_string(), s)

        self.chaos[0] = 1.0

    def test_chaos(self):
        s = 'Chaos([1.0])'

        self.assertEquals(repr(self.chaos), s)



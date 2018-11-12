import logging
import unittest

from pykit import ractdict
from pykit import ututil
from pykit import utfjson
from pykit.ractdict import Ractangle

dd = ututil.dd

logger = logging.getLogger(__name__)


class TestRange(unittest.TestCase):

    def test_intersect(self):
        a = Ractangle([5, 10], [2, 5], 1)

        cases = (
                # x cases
                ([[None, 5], [1, 3], 0],  None, ),
                ([[None, 6], [3, 4], 0],  [[5, 6], [3, 4], 1], ),
                ([[None, 10], [3, 4], 0], [[5, 10], [3, 4], 1], ),
                ([[None, 11], [3, 4], 0], [[5, 10], [3, 4], 1], ),
                ([[1, 11], [3, 4], 0],    [[5, 10], [3, 4], 1], ),
                ([[6, 11], [3, 4], 0],    [[6, 10], [3, 4], 1], ),
                ([[6, None], [3, 4], 0],  [[6, 10], [3, 4], 1], ),
                ([[10, 11], [3, 4], 0],   None, ),
                ([[10, None], [3, 4], 0], None, ),
                ([[None, None], [3, 4], 0], [[5, 10], [3, 4], 1], ),

                # y cases
                ([[6, 8], [None, 2], 0],    None),
                ([[6, 8], [None, 3], 0],    [[6, 8], [2, 3], 1], ),
                ([[6, 8], [None, 5], 0],    [[6, 8], [2, 5], 1], ),
                ([[6, 8], [None, 6], 0],    [[6, 8], [2, 5], 1], ),
                ([[6, 8], [1, 6], 0],       [[6, 8], [2, 5], 1], ),
                ([[6, 8], [3, 6], 0],       [[6, 8], [3, 5], 1], ),
                ([[6, 8], [3, None], 0],    [[6, 8], [3, 5], 1], ),
                ([[6, 8], [5, 7], 0],       None, ),
                ([[6, 8], [5, None], 0],    None, ),
                ([[6, 8], [None, None], 0], [[6, 8], [2, 5], 1], ),

                # 4 corner cases
                ([[0, 6], [0, 3], 0],  [[5, 6],  [2, 3], 1], ),
                ([[0, 6], [4, 7], 0],  [[5, 6],  [4, 5], 1], ),
                ([[8, 11], [0, 3], 0], [[8, 10], [2, 3], 1], ),
                ([[8, 11], [4, 7], 0], [[8, 10],  [4, 5], 1], ),
        )

        for b, expected in cases:

            dd('intersect:', a, b)
            dd('expected: ', expected)

            rst = a.intersect(b)
            self.assertEqual(expected, rst)

    def test_complement(self):

    def test_x(self):

        mp = Ractangle([0, 15], [0, 10], 'x')

        a = Ractangle([5, 10], [2, 5], 'a')
        b = Ractangle([2, 4], [2, 5], 'b')
        c = Ractangle([3, 7], [1, 4], 'c')

        d = c.intersect(a)
        subs = a.substract(c)
        subs = a.complement()
        subs = [x.intersect(mp) for x in subs]
        print subs
        subs = [x for x in subs if x is not None]

        for line in ractdict.draw(subs):
            print line

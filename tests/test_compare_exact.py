import unittest
import comparisons

class TestCompareExact(unittest.TestCase):

    def test_left_and_right_equal(self):
        resp = comparisons.compare_exact("foo", "foo", {}, {})
        assert resp is True

    def test_left_and_right_not_equal(self):
        resp = comparisons.compare_exact("foo", "bar", {}, {})
        assert resp is False





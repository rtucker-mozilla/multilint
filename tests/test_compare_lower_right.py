import unittest
import comparisons

class TestCompareLowerRight(unittest.TestCase):

    def test_left_and_right_equal(self):
        resp = comparisons.compare_lower_right("FOO", "foo", {}, {})
        assert resp is True

    def test_left_and_right_not_equal(self):
        resp = comparisons.compare_lower_right("FOO", "FOO", {}, {})
        assert resp is False
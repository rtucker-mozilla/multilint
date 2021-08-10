import unittest
import comparisons
from runners import parse_ldap_date

class TestRunnerParseLdapDate(unittest.TestCase):

    def test_date_object_i_string_as_bytes(self):
        i_string = b'20080929053433Z'
        date_obj = parse_ldap_date(i_string)
        assert date_obj.year == 2008

    def test_date_object_i_string_as_str(self):
        i_string = '20080929053433Z'
        date_obj = parse_ldap_date(i_string)
        assert date_obj.year == 2008
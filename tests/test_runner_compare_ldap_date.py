import unittest
import comparisons
from runners import parse_ldap_date, should_exclude_by_create_date

class TestRunnerCompareLDAPDate(unittest.TestCase):

    def test_exclude_exact_day(self):
        i_string =  b'20110111050000Z'
        i_string2 = b'20110118050000Z'
        today_date_obj = parse_ldap_date(i_string)
        create_date_obj = parse_ldap_date(i_string2)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == True

    def test_exclude_less_day(self):
        i_string =  b'20110111050000Z'
        i_string2 = b'20110115050000Z'
        today_date_obj = parse_ldap_date(i_string)
        create_date_obj = parse_ldap_date(i_string2)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == False

    def test_exclude_more_day(self):
        i_string =  b'20110111050000Z'
        i_string2 = b'20110119050000Z'
        today_date_obj = parse_ldap_date(i_string)
        create_date_obj = parse_ldap_date(i_string2)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == True
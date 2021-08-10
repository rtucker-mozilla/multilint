import unittest
import comparisons
from runners import parse_ldap_date, should_exclude_by_create_date

class TestRunnerCompareLDAPDate(unittest.TestCase):

    def test_exclude_exact_day(self):
        today_date_string =    b'20110118050000Z'
        new_hire_date_string = b'20110118050000Z'
        today_date_obj = parse_ldap_date(today_date_string)
        create_date_obj = parse_ldap_date(new_hire_date_string)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == True

    def test_exclude_account_created_within_six_days(self):
        today_date_string =    b'20110118050000Z'
        new_hire_date_string = b'20110112050000Z'
        today_date_obj = parse_ldap_date(today_date_string)
        create_date_obj = parse_ldap_date(new_hire_date_string)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == True

    def test_exclude_account_created_within_seven_days(self):
        today_date_string =    b'20110118050000Z'
        new_hire_date_string = b'20110111050000Z'
        today_date_obj = parse_ldap_date(today_date_string)
        create_date_obj = parse_ldap_date(new_hire_date_string)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == True

    def test_exclude_account_created_eight_days_ago_should_exclude_false(self):
        today_date_string =    b'20110118050000Z'
        new_hire_date_string = b'20110110050000Z'
        today_date_obj = parse_ldap_date(today_date_string)
        create_date_obj = parse_ldap_date(new_hire_date_string)
        assert should_exclude_by_create_date(create_date_obj, 7, today_date=today_date_obj) == False

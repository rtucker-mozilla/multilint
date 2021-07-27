import unittest
from runners import should_exclude_regex

settings_regex = {
    'exclude_regex': [
        r'.*_.*',
        r'.*receptionist@.*',
    ]
}

class TestExcludeRegex(unittest.TestCase):

    def test_exclude_underscore_true(self):
        true_uid = 'should_match@domain.com'
        should_exclude = should_exclude_regex(true_uid, settings_regex)
        assert should_exclude == True

    def test_exclude_office_receptionist(self):
        uid = 'pdxreceptionist@domain.com'
        should_exclude = should_exclude_regex(uid, settings_regex)
        assert should_exclude == True

    def test_exclude_receptionist(self):
        uid = 'receptionist@domain.com'
        should_exclude = should_exclude_regex(uid, settings_regex)
        assert should_exclude == True


    def test_shouldnt_match_regex(self):
        uid = 'shouldntmatch@domain.com'
        should_exclude = should_exclude_regex(uid, settings_regex)
        assert should_exclude == False
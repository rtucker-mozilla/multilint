import unittest
from pathlib import Path
import os
from runners import should_exclude_file

content = """excluded@domain.com
excluded2@domain.com"""

name = "Testing"
filename = "{}_exclusions.txt".format(name)

class TestExcludeFile(unittest.TestCase):

    def get_filepath(self):
        filename = "{}_exclusions.txt".format(name)
        project_path = Path(os.path.realpath(__file__)).parent.parent
        dir_path = os.path.join(project_path, "exclusions")
        filepath = os.path.join(dir_path, filename)
        return filepath

    def setUp(self):
        filepath = self.get_filepath()
        print(filepath)
        fh = open(filepath, 'w')
        fh.write(content)
        fh.close()

    def tearDown(self):
        filepath = self.get_filepath()
        os.unlink(filepath)


    def test_should_exclude_true(self):
        uid = "excluded@domain.com"
        should_exclude =  should_exclude_file(uid, name)
        assert should_exclude == True

    def test_should_exclude_last_entry(self):
        uid = "excluded2@domain.com"
        should_exclude =  should_exclude_file(uid, name)
        assert should_exclude == True

    def test_should_exclude_false(self):
        uid = "notexcluded@domain.com"
        should_exclude =  should_exclude_file(uid, name)
        assert should_exclude == False
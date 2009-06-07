import unittest
import sys
import os
import tempfile
from zc.buildout import testing
import zc.buildout


class UtilsTests(unittest.TestCase):
    """
    Test cases for the utility functions.
    """

    def test_repo_url(self):
        """
        Tests for get_reponame.
        """

        from zerokspot.recipe.git import get_reponame
        tests = (
                'http://domain.com/test/', 
                'http://domain.com/test.git', 
                'http://domain.com/test.git/',
                'http://domain.com/test',
                '/Users/test/repos/test'
                )
        for t in tests:
            self.assertEqual('test', get_reponame(t))

class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.tempcache = tempfile.mkdtemp()
        self.temprepo = os.path.join(self.tempcache, 'testrepo')
        os.mkdir(self.temprepo)
        testing.system('cd %s && git init' % self.temprepo)
        testing.write(self.temprepo, 'test.txt', 'TEST')
        testing.system('cd %s && git add test.txt && git commit -m "Init"' % self.temprepo)

    
    def testFetch(self):
        """
        Tests if the basic cloning of the repository works.
        """

        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo})
        testing.system('cd %s && buildout' % self.tempdir) 
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'parts', 'gittest', 'test.txt')))
    
    def testOffline(self):
        """
        Tests if install from the dowload-cache works.
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = %(cache)s
install-from-cache = true

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo, 'cache': self.tempcache})
        build = zc.buildout.buildout.Buildout(os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.install(None)
        self.assertTrue(build['gittest'].recipe.installed_from_cache)

    def tearDown(self):
        testing.rmdir(self.tempdir)
        testing.rmdir(self.temprepo)

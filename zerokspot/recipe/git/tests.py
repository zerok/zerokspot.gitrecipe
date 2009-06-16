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
        self.temprepos = tempfile.mkdtemp()
        self.repo_name = 'testrepo'
        self.temprepo = os.path.join(self.temprepos, self.repo_name)

        testing.mkdir(self.temprepo)

        os.chdir(self.tempdir)

        testing.system('cd %s && git init' % self.temprepo)
        testing.write(self.temprepo, 'test.txt', 'TEST')
        testing.system('cd %s && git add test.txt && git commit -m "Init"' % self.temprepo)


    def tearDown(self):
        testing.rmdir(self.tempdir)
        testing.rmdir(self.tempcache)
        testing.rmdir(self.temprepos)


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
        build = zc.buildout.buildout.Buildout(os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.install(None)
        self.assertTrue(os.path.exists(os.path.join(build['buildout']['download-cache'], self.repo_name, 'test.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'parts', 'gittest', 'test.txt')))

    #TODO RaiseExceptionOnAbsentCache

    def testOffline(self):
        """
        Tests if install from the dowload-cache works.
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = %(cache)s

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo, 'cache': self.tempcache})

        # First install as usual
        build = zc.buildout.buildout.Buildout(
                    os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.install(None)
        self.assertFalse(build['gittest'].recipe.installed_from_cache)

        # clear buildout
        os.unlink(os.path.join(build['buildout']['directory'], '.installed.cfg'))
        testing.rmdir(build['buildout']['directory'], 'parts')

        # now install from cache
        build = zc.buildout.buildout.Buildout(
                    os.path.join(self.tempdir, 'buildout.cfg'),
                    [('buildout', 'install-from-cache', 'true')])
        build.install(None)
        self.assertTrue(build['gittest'].recipe.installed_from_cache)

if __name__ == '__main__':
    sys.path.insert(0,  os.path.normpath(
                            os.path.join(
                                os.path.dirname(__file__) or os.getcwd(),
                                '../../../'
                            )))
    unittest.main()

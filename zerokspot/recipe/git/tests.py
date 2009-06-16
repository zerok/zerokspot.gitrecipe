import unittest
import sys
import os
import shutil
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
        # Prepare the cache
        os.mkdir(os.path.join(self.tempdir, 'downloads'))
        self.tempcache = tempfile.mkdtemp()
        self.temprepo = os.path.join(self.tempcache, 'testrepo')
        os.mkdir(self.temprepo)
        testing.system('cd %s && git init' % self.temprepo)
        testing.write(self.temprepo, 'test.txt', 'TEST')
        testing.system('cd %s && git add test.txt && git commit -m "Init"' % self.temprepo)
        testing.write(self.temprepo, 'test2.txt', 'TEST')
        testing.system('cd %s && git checkout -b test && git add test2.txt && git commit -m "Test-branch" && git checkout master' % self.temprepo)
        os.chdir(self.tempdir)

    def _buildout(self):
        build = zc.buildout.buildout.Buildout(os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.init(None)
        build.install(None)
        return build
    
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
        self._buildout()
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'parts', 'gittest', 'test.txt')))
    
    def testCacheCreation(self):
        """
        Tests if a normal download also fills the cache.
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = downloads

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
""" % {'repo' : self.temprepo })
        self._buildout()
        testing.ls(self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'downloads', 'testrepo')))

    def testFromCache(self):
        """
        Skip cache update on newest=="false"

        If the buildout's newest setting is set to "false" and the cache is filled, 
        the cache shouldn't receive an update.
        """
        shutil.copytree(self.temprepo, os.path.join(self.tempdir, 'downloads', 'test'))

        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = ./downloads
install-from-cache = true
newest = false

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo})
        build = zc.buildout.buildout.Buildout(os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.install(None)
        recipe = build['gittest'].recipe
        self.assertFalse(recipe.cache_updated)
        self.assertTrue(recipe.cache_cloned)

    def testNonstandardBranch(self):
        """
        Tests if install from the dowload-cache works with a non-standard branch.
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = %(cache)s
install-from-cache = true
offline = true

[gittest]
recipe = zerokspot.recipe.git
branch = test
repository = %(repo)s
        """ % {'repo' : self.temprepo, 'cache': self.tempcache})
        build = zc.buildout.buildout.Buildout(os.path.join(self.tempdir, 'buildout.cfg'), [])
        build.install(None)
        self.assertTrue(build['gittest'].recipe.installed_from_cache)


    def testOffline(self):
        """
        Tests if install from the dowload-cache works.
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
download-cache = %(cache)s
install-from-cache = true
offline = true

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo, 'cache': self.tempcache})
        build = self._buildout()
        self.assertTrue(build['gittest'].recipe.installed_from_cache)

    def testOfflineWithoutCache(self):
        """
        offline=='true' && no cache
        """
        testing.write(self.tempdir, 'buildout.cfg', """
[buildout]
parts = gittest
offline = true

[gittest]
recipe = zerokspot.recipe.git
repository = %(repo)s
        """ % {'repo' : self.temprepo})
        build = self._buildout()

    def tearDown(self):
        testing.rmdir(self.tempdir)
        testing.rmdir(self.temprepo)

"""
zerokspot.recipe.git is a small recipe that allows you to use git
repositories in a similar way like iw.recipe.subversion does for
subversion repositories::

    [myapp]
    recipe = zerokspot.recipe.git
    repository = <url-of-repository>
    branch = <name-of-branch> # default: "master"
    rev = <name-of-revision> # default: None
    newest = [true|false] # default: false, stay up to date even when
                          # when updating unless rev is set
    as_egg = [true|false] # default: false, install the fetched repo as
                          # egg
    cache-name = <name-in-download-cache> # default: None

This would store the cloned repository in ${buildout:directory}/parts/myapp.
"""

import sys
import os
import functools
import subprocess
import os.path
import zc.buildout
import shutil

def get_reponame(url):
    """
    Given the URL of a repository, this function returns the name of it after
    a clone process.
    """
    base = filter(lambda x: len(x), url.split('/'))[-1]
    if base.endswith('.git'):
        return base[:-4]
    return base

execute = functools.partial(subprocess.call, shell=True, stdout=open(os.devnull, 'w'), stderr=subprocess.PIPE)

class Recipe(object):
    """
    This recipe supports following options:

    repository
        Path to the repository that should be cloned

    branch
        Which branch should be cloned. If none is given, "master" is used by
        default.

    rev
        Revision that should be used. This is useful if you want to freeze
        the source at a given revision. If this is used, an update won't do
        all that much when executed.

    as_egg
        Set to True if you want the checkout to be registered as a
        development egg in your buildout.
    """
    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.cache_created = False
        self.cache_updated = False
        self.part_updated = False
        self.cache_cloned = False
        self.installed_from_cache = None
        self.repository = options['repository']
        self.branch = options.get('branch', 'master')
        self.rev = options.get('rev', None)
        self.newest = options.get('newest',
                buildout['buildout'].get('newest', "false")).lower() == 'true'
        self.offline = options.get('offline', 'false').lower() == 'true'
        self.cache_install = options.get('install-from-cache', 
                buildout['buildout'].get('install-from-cache', 'false')) \
                        .lower() == 'true'
        self.cache_name = options.get('cache-name', 
                get_reponame(self.repository))
        self.download_cache = self.buildout['buildout'].get('download-cache', None)
        if self.download_cache:
            self.cache_path = os.path.join(buildout['buildout']['download-cache'],
                    self.cache_name)
        self.root_dir = self.buildout['buildout']['directory'] 
        options['location'] = os.path.join(
                buildout['buildout']['parts-directory'], name)
        self.as_egg = options.get('as_egg', 'false').lower() == 'true'

    def _clone(self, from_, to):
        try:
            status = execute('git clone "%s" "%s"' %
                    (from_, to, ))
            if status != 0:
                raise zc.buildout.UserError("Couldn't clone %s into %s" % (
                    from_, to, ))
            os.chdir(to)
            if self.branch != 'master':
                branch = '-t "origin/%s"' %  (self.branch, )
            else:
                branch = '"master"'
            status = execute(r'git checkout %s' % branch)
            if status != 0:
                raise zc.buildout.UserError('Failed to switch to branch "%s" '
                    'in %s' % (self.branch, to, ))
            if self.rev is not None:
                status = execute(r'git checkout "%s"' % (self.rev,))
            if status != 0:
                raise zc.buildout.UserError("Failed to checkout revision")
        finally:
            os.chdir(self.root_dir)
    
    def _clone_cache(self):
        """
        Clone the cache into the parts directory.
        """
        if not os.path.exists(self.cache_path):
            self._clone_upstream()
        self._clone(self.cache_path, self.options['location'])
        self.cache_cloned = True

    def _clone_upstream(self):
        """
        Clone the upstream repository into the cache
        """
        self._clone(self.repository, self.cache_path)
        self.cache_created = True

    def _update_cache(self):
        """
        Updates the cached repository.
        """
        self._update_repository(self.cache_path)
        self.cache_updated = True

    def _update_part(self):
        """
        Updates the repository in the buildout's parts directory.
        """
        self._update_repository(self.options['location'])
        self.part_updated = True

    def _update_repository(self, path):
        """
        Update the repository from the given path
        """
        try:
            os.chdir(path)
            status = execute('git pull origin "%s"' % (self.branch))
            if status != 0:
                raise zc.buildout.UserError("Failed to pull")
        finally:
            os.chdir(self.root_dir)


    def install(self):
        """
        Method called when installing a part (or when the part's config
        was changed. It clones the the given git repository and checks
        out the requested branch or commit.

        Returns the path to the part's directory.
        """

        copy_to_cache = False
        self.installed_from_cache = False
        if self.offline:
            if not self.download_cache:
                raise zc.buildout.UserError("Offline mode requested and no download-cache specified")
            if os.path.exists(self.cache_path):
                # Just clone the cached repository
                self.installed_from_cache = True
                self._clone_cache()
            else:
                raise zc.buildout.UserError("Offline mode requested but the "
                        "requested repository doesn't exist in the cache")
        else:
            if self.download_cache:
                if self.newest:
                    # Update the cache before doing anything else
                    if not os.path.exists(self.cache_path):
                        self._clone_upstream()
                    self._update_cache()
                else:
                    self.installed_from_cache = True
                # Clone the cached repository
                self._clone_cache()
            else:
                # Go the direct way since we have no cache
                self._clone(self.repository, self.options['location'])
        if self.as_egg:
            self._install_as_egg()
        return self.options['location']

    def update(self):
        """
        Called when the buildout is called again without the local
        configuration having been altered. If no revision was
        requested and the newest-option enabled it tries to update the
        requested branch.
        """
        if self.rev is None and self.newest:
            # Do an update of the current branch
            print "Pulling updates from origin"
            if not self.cache_install:
                self._update_cache()
            self._update_part()
            os.chdir(self.options['location'])
            if self.as_egg:
                self._install_as_egg()
        else:
            # "newest" is also automatically disabled if "offline"
            # is set.
            print "Pulling disable for this part"

    def _install_as_egg(self):
        """
        Install clone as development egg.
        """
        path = self.options['location']
        target = self.buildout['buildout']['develop-eggs-directory']
        zc.buildout.easy_install.develop(path, target)

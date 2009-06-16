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

import subprocess
import os.path
import zc.buildout
import shutil


def git(operation, args, message):
    command = r'git %s ' + ' '.join(('"%s"',) * len(args))
    command = command % ((operation,) + tuple(args))
    status = subprocess.call(command, shell=True, stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT)
    if status != 0:
        raise zc.buildout.UserError(message)


def get_reponame(url, branch = None, rev = None):
    """
    Given the URL of a repository, this function returns the name of it after
    a clone process.
    """
    base = filter(lambda x: len(x), url.split('/'))[-1]
    if base.endswith('.git'):
        base = base[:-4]

    if rev != None or branch != None:
        base = base + '@' + (rev or branch)
    return base

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
        self.repository = options['repository']
        self.branch = options.get('branch', 'master')
        self.rev = options.get('rev', None)
        self.newest = options.get('newest',
                buildout['buildout'].get('newest', "false")).lower() == 'true'
        self.cache_install = options.get('install-from-cache', 
                buildout['buildout'].get('install-from-cache', 'false')) \
                        .lower() == 'true'
        self.cache_name = options.get('cache-name', 
                get_reponame(self.repository, self.branch, self.rev))
        self.cache_path = os.path.join(buildout['buildout']['download-cache'],
                self.cache_name)
        options['location'] = os.path.join(
                buildout['buildout']['parts-directory'], name)
        self.as_egg = options.get('as_egg', 'false').lower() == 'true'
        self.installed_from_cache = False

    def install(self):
        """
        Method called when installing a part (or when the part's config
        was changed. It clones the the given git repository and checks
        out the requested branch or commit.

        Returns the path to the part's directory.
        """

        if self.cache_install:
            # Check if a repo with the same name exists in the download cache
            # and copy it into parts/<part-name>. If there is nothing inside
            # the download cache, fetch the repo as usual and then copy it
            # into the download cache.
            if os.path.exists(self.cache_path):
                git('clone', (self.cache_path, self.options['location']),
                        'Failed to clone repository')

                os.chdir(self.buildout['buildout']['directory'])
                self.installed_from_cache = True
                return self.options['location']
            else:
                raise zc.buildout.UserError("No repository in the download "
                                            "cache directory.")
        else:
            os.chdir(self.buildout['buildout']['download-cache'])

            if os.path.exists(self.cache_path):
                shutil.rmtree(self.cache_path)

            git('clone', (self.repository, self.cache_name),
                    'Failed to clone repository')

            os.chdir(self.cache_path)
            if self.branch != 'master':
                branch = 'origin/%s' % (self.branch, )
            else:
                branch = 'master'

            git('checkout', (branch,), 'Failed to switch branch')

            if self.rev is not None:
                git('checkout', (self.rev,), 'Failed to checkout revision')

            git('clone', (self.cache_path, self.options['location']),
                    'Failed to clone repository')

            if self.as_egg:
                self._install_as_egg()

            os.chdir(self.buildout['buildout']['directory'])
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
            os.chdir(self.options['location'])
            try:
                git('pull origin', (self.branch), 'Failed to pull')

                if self.as_egg:
                    self._install_as_egg()
            finally:
                os.chdir(self.buildout['buildout']['directory'])
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


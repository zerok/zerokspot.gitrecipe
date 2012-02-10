.. important::
    
    This package is no longer actively maintained and therefor won't see any new
    features added to it. For more information please check out `the wiki <https://github.com/zerok/zerokspot.gitrecipe/wiki/EOL>`_

This simple recipe for zc.buildout fetches data from a given repository
and stores it into its part's directory. A simple task using this
could look like this::

    [myapp]
    recipe=zerokspot.recipe.git
    repository=git://github.com/zerok/zerokspot.gitrecipe.git
    rev=7c73978b55fcadbe2cd6f2abbefbedb5a85c2c8c

This would store the repository under ${buildout:directory}/parts/myapp
and keep it at exactly this revision, no matter what happens on the
server.

The recipe has following options:

repository
    The absolute URL of the repository to be fetched

rev
    A revision/commit within this repository the environment
    should use.

branch
    If you want to stay up to date with a certain branch other than
    "master", use this.

paths
    List of relative paths to packages to develop. Must be used together
    with as_egg=true.

newest
    This overrides the newest-option of the global setting for this
    part

as_egg
    Set to True if you want the checkout to be registered as a
    development egg in your buildout.

cache-name
    Name of the repository in the download-cache directory.

recursive
    Follow submodules (Note that submodules are not cloned from the download
    cache).


Offline installation
--------------------

If you want to install a part from the download-cache, this is now possible, too::
    
    [buildout]
    parts = myapp
    download-cache = /var/cache/buildout
    install-from-cache = true

    [mylib]
    recipe = zerokspot.recipe.git
    repository = http://domain.com/repo.git

With this configuration, the recipe will look for /var/cache/buildout/repo and
clone it into the local parts/ folder.

The recipe also supports an additional "cache-name" setting that lets you
configure the folder name of the repository in the download cache.


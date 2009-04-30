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

newest
    This overrides the newest-option of the global setting for this
    part

as_egg
    Set to True if you want the checkout to be registered as a
    development egg in your buildout.

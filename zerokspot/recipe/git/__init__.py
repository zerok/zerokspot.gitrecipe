import subprocess
import os.path
import zc.buildout

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
    """
    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.repository = options['repository']
        self.branch = options.get('branch', 'master')
        self.rev = options.get('rev', None)
        self.newest = options.get('newest', 
                buildout['buildout'].get('newest', "false")).lower() == 'true'
        self.target = os.path.join(buildout['buildout']['directory'], 
                'parts', name)

    def install(self):
        ec = subprocess.call(r'git clone "%s" "%s"' % 
                (self.repository, self.target), shell=True)
        if ec != 0:
            raise zc.buildout.UserError("Failed to clone repository")
        try:
            os.chdir(self.target)
            
            ec = subprocess.call(r'git checkout "origin/%s"' % (self.branch,),
                    shell=True)
            if ec != 0:
                raise zc.buildout.UserError("Failed to switch branch")

            if self.rev is not None:
                ec = subprocess.call(r'git checkout "%s"' % (self.rev,),
                        shell=True)
            if ec != 0:
                raise zc.buildout.UserError("Failed to checkout revision")
        finally:
            os.chdir(self.buildout['buildout']['directory'])
            return self.target

    def update(self):
        if self.rev is None and self.newest:
            # Do an update of the current branch
            print "Pulling updates from origin"
            os.chdir(self.target)
            try:
                ec = subprocess.call('git pull origin "%s"' % (self.branch),
                        shell=True)
                if ec != 0:
                    raise zc.buildout.UserError("Failed to pull")
            finally:
                os.chdir(self.buildout['buildout']['directory'])
        else:
            print "Pulling disable for this part"

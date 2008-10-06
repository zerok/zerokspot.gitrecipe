from setuptools import setup, find_packages

setup(
        name='zerokspot.recipe.git',
        author='Horst Gutmann',
        author_email='zerok@zerokspot.com',
        version = '0.1',
        install_requires = ['setuptools', 'zc.buildout'],
        namespace_packages = ['zerokspot'],
        packages = find_packages(exclude=['ez_setup']),
        entry_points = {'zc.buildout': ['default = zerokspot.recipe.git:Recipe']}
        )

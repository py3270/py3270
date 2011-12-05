import sys, os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as STDevelopCmd

from py3270 import VERSION

cdir = os.path.abspath(os.path.dirname(__file__))
readme_rst = open(os.path.join(cdir, 'readme.rst')).read()
changelog_rst = open(os.path.join(cdir, 'changelog.rst')).read()

class DevelopCmd(STDevelopCmd):
    def run(self):
        # add in requirements for testing only when using the develop command
        self.distribution.install_requires.extend([
            'nose',
            'mock>=0.7.999',
            'blazeutils',
            'coverage',
        ])
        STDevelopCmd.run(self)

setup(
    name='py3270',
    version=VERSION,
    description="A Python interface to x3270, an IBM 3270 terminal emulator",
    long_description= readme_rst + '\n\n' + changelog_rst,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Terminals :: Terminal Emulators/X Terminals'
    ],
    author='Randy Syring',
    author_email='rsyring@gmail.com',
    url='https://bitbucket.org/rsyring/py3270',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    cmdclass = {
        'develop': DevelopCmd
    },
)

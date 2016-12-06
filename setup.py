import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as STDevelopCmd

cdir = os.path.abspath(os.path.dirname(__file__))
readme_rst = open(os.path.join(cdir, 'readme.rst')).read()
changelog_rst = open(os.path.join(cdir, 'changelog.rst')).read()
VERSION = open(os.path.join(cdir, 'py3270', 'version.txt')).read().strip()


class DevelopCmd(STDevelopCmd):
    def run(self):
        # add in requirements for testing only when using the develop command
        self.distribution.install_requires.extend([
            'nose',
            'mock',
            'blazeutils',
            'coverage',
        ])
        STDevelopCmd.run(self)

setup(
    name='py3270',
    version=VERSION,
    description="A Python interface to x3270, an IBM 3270 terminal emulator",
    long_description=readme_rst + '\n\n' + changelog_rst,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Terminals :: Terminal Emulators/X Terminals'
    ],
    author='Randy Syring',
    author_email='randy@thesyrings.us',
    url='https://bitbucket.org/rsyring/py3270',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['six'],
    cmdclass={
        'develop': DevelopCmd
    },
)

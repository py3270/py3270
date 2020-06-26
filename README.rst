
|license| |pypi| |coverage| |bugs| |code smells| |vulnerabilities|
|duplicated lines|

Intro
-----

py3270 is a Python interface to x3270, an IBM 3270 terminal emulator.
It provides an API to a x3270 or s3270 subprocess.

Example
--------

The x3270 executables need to be on your PATH!

A brief example of usage:

.. code:: python

    from py3270 import Emulator

    # use x3270 so you can see what is going on
    em = Emulator(visible=True)

    # or not (uses s3270)
    em = Emulator()

    em.connect('3270host.example.com')
    em.fill_field(17, 23, 'mylogin', 8)
    em.fill_field(18, 23, 'mypass', 8)
    em.send_enter()

    # if your host unlocks the keyboard before truly being ready you can use:
    em.wait_for_field()

    # maybe look for a status message
    if not em.string_found(1, 2, 'login successful'):
        abort()

    # do something useful

    # disconnect from host and kill subprocess
    em.terminate()

Documentation
--------------

None, sorry. Read the code, its pretty simple & self-explanatory  :)

More information on x3270/s3270 can be found at:

* http://x3270.bgp.nu/
* http://x3270.bgp.nu/x3270-man.html
* http://x3270.bgp.nu/s3270-man.html
* http://x3270.bgp.nu/x3270-script.html

Questions & Comments
---------------------

Please submit a issue or visit: http://groups.google.com/group/blazelibs

Current Status
---------------

The interface seems sound, but the Emulator class has only basic functionality.
There are more x3270 commands that the Emulator could have methods for. That
being said, I believe most x3270 functionality can be supported at a lower-level
by the use of Emulator.exec_command().

py3270 is installable via `pip` with ``pip install py3270`` or `easy_install`
with ``easy_install py3270``.

.. |license| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://opensource.org/licenses/BSD-3-Clause
    :alt: BSD-3-Clause

.. |pypi| image:: https://img.shields.io/pypi/v/py3270.svg
    :target: https://pypi.python.org/pypi/py3270
    :alt: Latest version released on PyPi

.. |coverage| image:: https://sonarcloud.io/api/project_badges/measure?project=py3270&metric=coverage
    :target: https://sonarcloud.io/component_measures?id=py3270&metric=coverage
    :alt: Test coverage

.. |bugs| image:: https://sonarcloud.io/api/project_badges/measure?project=py3270&metric=bugs
    :target: https://sonarcloud.io/component_measures?id=py3270&metric=bugs
    :alt: Bugs

.. |code smells| image:: https://sonarcloud.io/api/project_badges/measure?project=py3270&metric=code_smells
    :target: https://sonarcloud.io/component_measures?id=py3270&metric=code_smells
    :alt: Code Smells

.. |vulnerabilities| image:: https://sonarcloud.io/api/project_badges/measure?project=py3270&metric=vulnerabilities
    :target: https://sonarcloud.io/component_measures?id=py3270&metric=vulnerabilities
    :alt: Vulnerabilities

.. |duplicated lines| image:: https://sonarcloud.io/api/project_badges/measure?project=py3270&metric=duplicated_lines_density
    :target: https://sonarcloud.io/component_measures?id=py3270&metric=duplicated_lines_density
    :alt: Duplicated Lines Density

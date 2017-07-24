Change Log
----------

0.3.4 released 2017-07-24
============================

- Fix BrokenPipeError issue WRT Python 2.7

0.3.3 released 2016-01-21
=========================

- continued fix to broken version import (include version in manifest)

0.3.2 released 2016-01-21
=========================

- fix broken version import in setup.py (broken in 0.3.0 and 0.3.1)

0.3.1 released 2016-01-21
=========================

- fix testing support for Python 3
- fix Windows support for Python 3
- move to github, related updates to vcs-specific files

0.3.0 released 2015-07-29
=========================

- Support Python 3

0.2.0 released 2014-03-28
=========================

- Add Windows support, but not tested thoroughly.  Consider Windows support Experimental.
- use x3270 executables from PATH instead of requiring ExamBase to be subclassed
- fix buffering problems when writing to x3270 subprocess

0.1.5 released 2013-06-17
=========================

- changed default timeout to 30 seconds
- added send_pf7(), send_pf8()

0.1.4 released 2012-03-17
=========================

- added is_connected() method

0.1.3 released 2011-12-06
=========================

- had messed up a previous upload to pypi releasing a fixed 0.1.1 as 0.1.2, so
    need to go to next version number

0.1.2 released 2011-12-06
=========================

- fix data parsing on Windows

0.1.1 released 2011-12-05
=========================

- renamed Emulator to EmulatorBase to make it clearer that a subclass is needed
- adjusted readme

0.1.0 released 2011-12-01
=========================

- initial release

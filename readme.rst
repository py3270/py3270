Intro
-----

py3270 is a Python interface to x3270, an IBM 3270 terminal emulator.  It
provides an API to a x3270 or s3270 subprocess.

Example
--------

A brief example of usage::

    from py3270 import EmulatorBase

    class Emulator(EmulatorBase):
        x3270_executable = '/fake/x3270'
        s3270_executable = '/fake/s3270'

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
    if not em.string_found(1, 2, 'login succesful'):
        abort()

    # do something useful

    # disconnect from host and kill subprocess
    em.terminate()

Documentation
--------------

None.  Read the code, its pretty self-explanatory  :)

More information on x3270/s3270 can be found at:

* http://x3270.bgp.nu/
* http://x3270.bgp.nu/x3270-man.html
* http://x3270.bgp.nu/s3270-man.html
* http://x3270.bgp.nu/x3270-script.html

Questions & Comments
---------------------

Please visit: http://groups.google.com/group/blazelibs

Current Status
---------------

The interface seems sound, but the Emulator class has only basic functionality.
There are more x3270 commands that the Emulator could have methods for. That
being said, I believe most x3270 functionality can be supported at a lower-level
by the use of Emulator.exec_command().

The `py3270 tip <http://bitbucket.org/rsyring/py3270/get/tip.zip#egg=py3270-dev>`_
is installable via `easy_install` with ``easy_install py3270==dev``.

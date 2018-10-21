Intro
-----

py3270 is a Python interface to x3270, an IBM 3270 terminal emulator.  It
provides an API to a x3270 or s3270 subprocess.

Example
--------

The x3270 executables need to be on your PATH!

A brief example of usage::

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
    if not em.string_found(1, 2, 'login succesful'):
        abort()

    # do something useful

    # disconnect from host and kill subprocess
    em.terminate()

Documentation
--------------

None, sorry.  Read the code, its pretty simple & self-explanatory  :)

More information on x3270/s3270 can be found at:

* http://x3270.bgp.nu/
* http://x3270.bgp.nu/x3270-man.html
* http://x3270.bgp.nu/s3270-man.html
* http://x3270.bgp.nu/x3270-script.html

Upgrading from 0.1.x to 0.2.0
-----------------------------

There are some backwards incompatable changes from 0.1.5 to 0.2.0.  Namely:

* x3270 executables now need to be on the PATH
* Don't use x3270.EmulatorBase, use x3270.Emulator instead.  Its the same API exect that you no
  longer need to specify the paths to the x3270 executables.
* the underlying Command object and some internal APIs have changed.  If you were digging into the
  Emulator instance to change things, you may have problems.  See the source, the changes weren't
  major and shouldn't be too hard to fix.

Questions & Comments
---------------------

Please visit: http://groups.google.com/group/blazelibs

Current Status
---------------

The interface seems sound, but the Emulator class has only basic functionality.
There are more x3270 commands that the Emulator could have methods for. That
being said, I believe most x3270 functionality can be supported at a lower-level
by the use of Emulator.exec_command().

py3270 is installable via `pip` with ``pip install py3270`` or `easy_install` with
``easy_install py3270``.

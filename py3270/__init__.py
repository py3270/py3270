import logging
from os import path as osp
import subprocess
import time

log = logging.getLogger(__name__)

VERSION = '0.1.4'

class CommandError(Exception):
    pass

class TerminatedError(Exception):
    pass

class WaitError(Exception):
    pass

class KeyboardStateError(Exception):
    pass

class FieldTruncateError(Exception):
    pass

class Command(object):
    """
        Represents a x3270 script command
    """
    def __init__(self, sp, cmdstr):
        self.sp = sp
        self.cmdstr = cmdstr
        self.status_line = None
        self.data = []

    def execute(self):
        self.sp.stdin.write(self.cmdstr + '\n')

        # x3270 puts data lines (if any) on stdout prefixed with 'data: '
        # followed by two more lines without the prefix.
        # 1: status of the emulator
        # 2: 'ok' or 'error' indicating whether the command succeeded or failed
        while True:
            line = self.sp.stdout.readline()
            log.debug('stdout line: %s', line.rstrip())
            if not line.startswith('data:'):
                # ok, we are at the status line
                self.status_line = line.rstrip()
                result = self.sp.stdout.readline().rstrip()
                log.debug('result line: %s', result)
                return self.handle_result(result)

            # remove the 'data: ' prefix and trailing newline char(s) and store
            self.data.append(line[6:].rstrip('\n\r'))

    def handle_result(self, result):
        # should receive 'ok' for almost everything, but Quit returns a '' for
        # some reason
        if result == '' and self.cmdstr == 'Quit':
            return
        if result == 'ok':
            return
        if result != 'error':
            raise ValueError('expected "ok" or "error" result, but received: {0}'.format(result))

        msg = '[no error message]'
        if self.data:
            msg = ''.join(self.data).rstrip()
        raise CommandError(msg)

class Status(object):
    """
        Represents a status line as returned by x3270 following a command
    """
    def __init__(self, status_line):
        if not status_line:
            status_line = ' '*12
        parts = status_line.split(' ')
        self.as_string = status_line.rstrip()
        self.keyboard = parts[0] or None
        self.screen_format = parts[1] or None
        self.field_protection = parts[2] or None
        self.connection_state = parts[3] or None
        self.emulator_mode = parts[4] or None
        self.model_number = parts[5] or None
        self.row_number = parts[6] or None
        self.col_number = parts[7] or None
        self.cursor_row = parts[8] or None
        self.cursor_col = parts[9] or None
        self.window_id = parts[10] or None
        self.exec_time = parts[11] or None

    def __str__(self):
        return 'STATUS: {0}'.format(self.as_string)

class EmulatorBase(object):
    """
        Represents an x/s3270 emulator subprocess and provides an API for interacting
        with it.
    """

    # these should be overriden in a subclass
    x3270_executable = None
    s3270_executable = None

    # additional command line args to the executable
    x3270_args = ['-script']
    s3270_args = []

    # arguments that apply to either executable
    args_for_either = [
        # Per Paul Mattes, in the first days of x3270, there were servers that
        # would unlock the keyboard before they had processed the command. To
        # work around that, when AID commands are sent, there is a 350ms delay
        # before the command returns. This arg turns that feature off for
        # performance reasons.
        '-xrm', 's3270.unlockDelay: False'
    ]

    def __init__(self, visible=False, timeout=3, _sp=None):
        """
            Create an emulator instance

            `visible` controls which executable will be used.
            `timeout` controls the timeout paramater to any Wait() command sent
                to x3270.
            `_sp` is normally not used but can be set to a mock object
                during testing.
        """
        if visible:
            args = [self.x3270_executable] + self.x3270_args + self.args_for_either
        else:
            args = [self.s3270_executable] + self.s3270_args + self.args_for_either

        # use _sp for passing in mock objects during testing
        self.sp = _sp or subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.is_terminated = False
        self.status = Status(None)
        self.timeout = timeout
        self.last_host = None

    def exec_command(self, cmdstr):
        """
            Execute an x3270 command

            `cmdstr` gets sent directly to the x3270 subprocess on it's stdin.
        """
        if self.is_terminated:
            raise TerminatedError('this TerminalClient instance has been terminated')

        log.debug('sending command: %s', cmdstr)
        c = Command(self.sp, cmdstr)
        start = time.time()
        c.execute()
        elapsed = time.time() - start
        log.debug('elapsed execution: {0}'.format(elapsed))
        self.status = Status(c.status_line)

        return c

    def terminate(self):
        """
            terminates the underlying x3270 subprocess. Once called, this
            Emulator instance must no longer be used.
        """
        if not self.is_terminated:
            log.debug('terminal client terminated')
            self.exec_command('Quit')
            self.is_terminated = True

    def is_connected(self):
        """
            Return bool indicating connection state
        """
        # this is basically a no-op, but it results in the the current status
        # getting updated
        self.exec_command('ignore')

        # connected status is like 'C(192.168.1.1)', disconnected is 'N'
        return self.status.connection_state.startswith('C(')

    def connect(self, host):
        """
            Connect to a host
        """
        self.exec_command('Connect({0})'.format(host))
        self.last_host = host

    def reconnect(self):
        """
            Disconnect from the host and re-connect to the same host
        """
        self.exec_command('Disconnect')
        self.connect(self.last_host)

    def wait_for_field(self):
        """
            Wait until the screen is ready, the cursor has been positioned
            on a modifiable field, and the keyboard is unlocked.

            Sometimes the server will "unlock" the keyboard but the screen will
            not yet be ready.  In that case, an attempt to read or write to the
            screen will result in a 'E' keyboard status because we tried to
            read from a screen that is not yet ready.

            Using this method tells the client to wait until a field is
            detected and the cursor has been positioned on it.
        """
        self.exec_command('Wait({0}, InputField)'.format(self.timeout))
        if self.status.keyboard != 'U':
            raise KeyboardStateError('keyboard not unlocked, state was: {0}'.format(self.status.keyboard))

    def move_to(self, ypos, xpos):
        """
            move the cursor to the given co-ordinates.  Co-ordinates are 1
            based, as listed in the status area of the terminal.
        """
        # the screen's co-ordinates are 1 based, but the command is 0 based
        xpos -= 1
        ypos -= 1
        self.exec_command('MoveCursor({0}, {1})'.format(ypos, xpos))

    def send_string(self, tosend, ypos=None, xpos=None):
        """
            Send a string to the screen at the current cursor location or at
            screen co-ordinates `ypos`/`xpos` if they are both given.

            Co-ordinates are 1 based, as listed in the status area of the
            terminal.
        """
        if xpos is not None and ypos is not None:
            self.move_to(ypos, xpos)

        # escape double quotes in the data to send
        tosend = tosend.replace('"', '\"')

        self.exec_command('String("{0}")'.format(tosend))

    def send_enter(self):
        self.exec_command('Enter')

    def send_pf3(self):
        self.exec_command('PF(3)')

    def send_pf4(self):
        self.exec_command('PF(4)')

    def send_pf5(self):
        self.exec_command('PF(5)')

    def send_pf6(self):
        self.exec_command('PF(6)')

    def string_get(self, ypos, xpos, length):
        """
            Get a string of `length` at screen co-ordinates `ypos`/`xpos`

            Co-ordinates are 1 based, as listed in the status area of the
            terminal.
        """
        # the screen's co-ordinates are 1 based, but the command is 0 based
        xpos -= 1
        ypos -= 1
        cmd = self.exec_command('Ascii({0},{1},{2})'.format(ypos, xpos, length))
        # this usage of ascii should only return a single line of data
        assert len(cmd.data) == 1, cmd.data
        return cmd.data[0]

    def string_found(self, ypos, xpos, string):
        """
            Return True if `string` is found at screen co-ordinates
            `ypos`/`xpos`, False otherwise.

            Co-ordinates are 1 based, as listed in the status area of the
            terminal.
        """
        if self.string_get(ypos, xpos, len(string)) == string:
            return True
        return False

    def delete_field(self):
        """
            Delete contents in field at current cursor location and positions
            cursor at beginning of field.
        """
        self.exec_command('DeleteField')

    def fill_field(self, ypos, xpos, tosend, length):
        """
            clears the field at the position given and inserts the string
            `tosend`

            tosend: the string to insert
            length: the length of the field

            Co-ordinates are 1 based, as listed in the status area of the
            terminal.

            raises: FieldTruncateError if `tosend` is longer than
                `length`.
        """
        if length - len(tosend) < 0:
            raise FieldTruncateError('length limit %d, but got "%s"' % (length, tosend))
        if xpos is not None and ypos is not None:
            self.move_to(ypos, xpos)
        self.delete_field()
        self.send_string(tosend)

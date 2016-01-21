from io import BytesIO
import subprocess

from blazeutils.testing import raises
import mock
from nose.plugins.skip import SkipTest
from nose.tools import eq_

from py3270 import EmulatorBase, Emulator, Command, Status, FieldTruncateError, \
    TerminatedError, KeyboardStateError, CommandError


class MEmulator(Emulator):
    def __init__(self, visible=False, timeout=3):
        Emulator.__init__(self, visible, timeout)


class MCommand(Command):
    def __init__(self, data='', result='ok', cmdstr=b'testcmd'):
        Command.__init__(self, ExamApp(data, result), cmdstr)


class ExamApp(object):
    """ An object with an interface like ExecutableApp used for testing """

    def __init__(self, data='', result='ok'):
        self.stdin = BytesIO()

        response = data
        response += '' * 12 + '\n'
        response += result + '\n'
        self.stdout = BytesIO(response.encode('ascii'))

    def connect(self, host):
        return False

    def close(self):
        self.stdin.close()

    def write(self, data):
        self.stdin.write(data)
        self.stdin.flush()

    def readline(self):
        return self.stdout.readline()


class TestStatus(object):

    def test_empty(self):
        s = Status(None)
        eq_(s.as_string, '')
        eq_(s.keyboard, None)

    def test_split(self):
        statstr = b'U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082'
        s = Status(statstr)
        eq_(s.as_string, statstr.decode('ascii'))
        eq_(s.keyboard, b'U')

    def test_str_magic(self):
        statstr = b'U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082'
        s = Status(statstr)
        eq_(str(s), 'STATUS: ' + statstr.decode('ascii'))


class TestEmulator(object):

    @mock.patch('py3270.Emulator.exec_command')
    def test_connect(self, m_ec):
        em = MEmulator()
        assert em.last_host is None
        em.connect('localhost')
        assert em.last_host == 'localhost'
        m_ec.assert_called_once_with(b'Connect(localhost)')

    @mock.patch('py3270.Emulator.exec_command')
    def test_terminate(self, m_ec):
        em = MEmulator()
        em.terminate()
        m_ec.assert_called_once_with(b'Quit')
        assert em.is_terminated

    @raises(TerminatedError)
    @mock.patch('py3270.Command')
    def test_command_after_terminate(self, m_cmd):
        em = MEmulator()
        em.terminate()
        em.connect('localhost')

    @mock.patch('py3270.Emulator.exec_command')
    def test_exec_methods(self, m_ec):
        em = MEmulator()

        em.send_enter()
        m_ec.assert_called_with(b'Enter')

        em.send_string('foo"bar')
        m_ec.assert_called_with(b'String("foo\"bar")')

        em.move_to(5, 7)
        m_ec.assert_called_with(b'MoveCursor(4, 6)')

        em.send_pf3()
        m_ec.assert_called_with(b'PF(3)')

        em.send_pf4()
        m_ec.assert_called_with(b'PF(4)')

        em.send_pf5()
        m_ec.assert_called_with(b'PF(5)')

        em.send_pf6()
        m_ec.assert_called_with(b'PF(6)')

        m_ec.reset_mock()
        em.send_string('foobar', 5, 7)
        eq_(
            m_ec.call_args_list,
            [
                mock.call(b'MoveCursor(4, 6)'),
                mock.call(b'String("foobar")'),
            ]
        )

    @mock.patch('py3270.Emulator.connect')
    @mock.patch('py3270.Emulator.exec_command')
    def test_reconnect(self, m_ec, m_connect):
        em = MEmulator()
        em.last_host = 'foo'
        em.reconnect()
        eq_(m_ec.call_args_list[0], mock.call(b'Disconnect'))
        eq_(
            m_connect.call_args_list,
            [
                # call from reconnect()
                mock.call('foo'),
            ]
        )

    @mock.patch('py3270.Emulator.exec_command')
    def test_fill_field(self, m_ec):
        em = MEmulator()

        em.fill_field(7, 9, 'foobar', 6)
        eq_(
            m_ec.call_args_list,
            [
                mock.call(b'MoveCursor(6, 8)'),
                mock.call(b'DeleteField'),
                mock.call(b'String("foobar")'),
            ]
        )
        m_ec.reset_mock()

        em.fill_field(None, None, 'foobar', 6)
        eq_(
            m_ec.call_args_list,
            [
                mock.call(b'DeleteField'),
                mock.call(b'String("foobar")'),
            ]
        )
        m_ec.reset_mock()

        em.fill_field(1, None, 'foobar', 6)
        eq_(
            m_ec.call_args_list,
            [
                mock.call(b'DeleteField'),
                mock.call(b'String("foobar")'),
            ]
        )

    @mock.patch('py3270.Emulator.exec_command')
    def test_string_get(self, m_ec):
        em = MEmulator()
        m_ec.return_value.data = [b'foobar']
        result = em.string_get(7, 9, 5)
        eq_(result, 'foobar')
        m_ec.assert_called_with(b'Ascii(6,8,5)')
        em.terminate()

    @raises(AssertionError)
    @mock.patch('py3270.Emulator.exec_command')
    def test_string_get_too_much_data(self, m_ec):
        em = MEmulator()
        m_ec.return_value.data = ['foobar', 'baz']
        em.string_get(7, 9, 5)

    @mock.patch('py3270.Emulator.string_get')
    def test_string_found(self, m_string_get):
        em = MEmulator()
        m_string_get.return_value = 'foobar'

        assert em.string_found(7, 9, 'foobar')
        m_string_get.assert_called_once_with(7, 9, 6)

        assert not em.string_found(7, 9, 'baz')

    @raises(FieldTruncateError, 'length limit 5, but got "foobar"')
    def test_fill_field_length_error(self):
        em = MEmulator()
        em.fill_field(1, 1, 'foobar', 5)

    @mock.patch('py3270.Emulator.exec_command')
    def test_wait_for_field(self, m_ec):
        em = MEmulator()
        em.status.keyboard = b'U'
        em.wait_for_field()

        m_ec.assert_called_once_with(b'Wait(3, InputField)')

    @mock.patch('py3270.Emulator.exec_command')
    def test_wait_for_field_custom_timeout(self, m_ec):
        em = MEmulator(timeout=5)
        em.status.keyboard = b'U'
        em.wait_for_field()

        m_ec.assert_called_once_with(b'Wait(5, InputField)')

    @raises(KeyboardStateError, 'keyboard not unlocked, state was: E')
    @mock.patch('py3270.Emulator.exec_command')
    def test_wait_for_field_exception(self, m_ec):
        em = MEmulator()
        em.status.keyboard = b'E'
        em.wait_for_field()

    @mock.patch('py3270.Emulator.exec_command')
    def test_not_is_connected(self, m_ec):
        em = MEmulator()

        def assign_status(*args, **kwargs):
            em.status.connection_state = b'N'
        m_ec.side_effect = assign_status
        assert not em.is_connected()
        m_ec.assert_called_once_with(b'ignore')

    @mock.patch('py3270.Emulator.exec_command')
    def test_is_connected(self, m_ec):
        em = MEmulator()

        def assign_status(*args, **kwargs):
            em.status.connection_state = b'C(192.168.1.1)'
        m_ec.side_effect = assign_status
        assert em.is_connected()
        m_ec.assert_called_once_with(b'ignore')

    @raises(Exception, 'EmulatorBase has been replaced by Emulator.')
    def test_emulatorbase_exception(self):
        EmulatorBase()


class TestCommand(object):

    def test_defaults(self):
        cmd = MCommand()
        eq_(cmd.cmdstr, b'testcmd')
        eq_(cmd.status_line, None)
        eq_(cmd.data, [])

    @mock.patch.object(ExamApp, 'write')
    def test_stdin(self, m_write):
        cmd = MCommand()
        cmd.execute()
        cmd.app.write.assert_called_once_with(b'testcmd\n')

    def test_data(self):
        data = 'data: foo\n'
        data += 'data: bar\n'
        cmd = MCommand(data)
        cmd.execute()
        eq_(cmd.data, [b'foo', b'bar'])

    def test_data_windows_line_endings(self):
        data = 'data: foo\r\n'
        data += 'data: bar\r\n'
        cmd = MCommand(data)
        cmd.execute()
        eq_(cmd.data, [b'foo', b'bar'])

    @raises(CommandError, 'some kind of error')
    def test_error_response(self):
        data = 'data: some kind \n'
        data += 'data: of error\n'
        cmd = MCommand(data, result='error')
        cmd.execute()

    @raises(CommandError, '[no error message]')
    def test_error_response_no_data(self):
        cmd = MCommand(result='error')
        cmd.execute()

    @raises(ValueError, 'expected "ok" or "error" result, but received: foobar')
    def test_unexpected_result(self):
        cmd = MCommand(result='foobar')
        cmd.execute()

    @raises(ValueError, 'expected "ok" or "error" result, but received: ')
    def test_blank_result(self):
        cmd = MCommand(result='')
        cmd.execute()

    def test_blank_result_with_quit(self):
        cmd = MCommand(result='', cmdstr=b'Quit')
        # running without exception is sufficient for this test
        cmd.execute()


class TestExecutableApp(object):
    """
        all these tests used to be part of the emulator testing, but they need to be refactored
        now that we are using ExecutableApp

    """
    def setUp(object):
        raise SkipTest

    @mock.patch('py3270.subprocess.Popen')
    def test_sp_creation(self, m_popen):
        em = TEmulator()
        m_popen.assert_called_once_with(
            ['/fake/s3270', '-xrm', 's3270.unlockDelay: False'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert not em.is_terminated
        eq_(em.status.as_string, '')
        eq_(em.status.keyboard, None)

    @mock.patch('py3270.subprocess.Popen')
    def test_visible_setting(self, m_popen):
        TEmulator(visible=True)
        eq_(m_popen.call_args[0][0][0], '/fake/x3270')

    @mock.patch('py3270.subprocess.Popen')
    def test_sp_creation_for_testing(self, m_popen):
        TEmulator(_sp=mock.Mock())
        assert not m_popen.called

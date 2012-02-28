from cStringIO import StringIO
import subprocess

from blazeutils.testing import raises
import mock
from nose.tools import eq_

from py3270 import EmulatorBase, Command, Status, FieldTruncateError, \
    TerminatedError, KeyboardStateError, CommandError

class TEmulator(EmulatorBase):
    x3270_executable = '/fake/x3270'
    s3270_executable = '/fake/s3270'

class MEmulator(TEmulator):
    def __init__(self, visible=False, timeout=3):
        TEmulator.__init__(self, visible, timeout, _sp=mock.Mock())

class MCommand(Command):
    def __init__(self, data='', result='ok', cmdstr='testcmd'):
        Command.__init__(self, mock.Mock(), cmdstr)
        response = data
        response += '' * 12 + '\n'
        response += result + '\n'
        self.sp.stdout = StringIO(response)

class TestStatus(object):

    def test_empty(self):
        s = Status(None)
        eq_(s.as_string, '')
        eq_(s.keyboard, None)

    def test_split(self):
        statstr = 'U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082'
        s = Status(statstr)
        eq_(s.as_string, statstr)
        eq_(s.keyboard, 'U')

    def test_str_magic(self):
        statstr = 'U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082'
        s = Status(statstr)
        eq_(str(s), 'STATUS: ' + statstr)

class TestEmulator(object):

    @mock.patch('py3270.subprocess.Popen')
    def test_sp_creation(self, m_popen):
        em =  TEmulator()
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
        em =  TEmulator(_sp=mock.Mock())
        assert not m_popen.called

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_connect(self, m_ec):
        em =  MEmulator()
        assert em.last_host is None
        em.connect('localhost')
        assert em.last_host == 'localhost'
        m_ec.assert_called_once_with('Connect(localhost)')

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_terminate(self, m_ec):
        em =  MEmulator()
        em.terminate()
        m_ec.assert_called_once_with('Quit')
        assert em.is_terminated

    @raises(TerminatedError)
    @mock.patch('py3270.Command')
    def test_command_after_terminate(self, m_cmd):
        em =  MEmulator()
        em.terminate()
        em.connect('localhost')

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_exec_methods(self, m_ec):
        em =  MEmulator()

        em.send_enter()
        m_ec.assert_called_with('Enter')

        em.send_string('foo"bar')
        m_ec.assert_called_with('String("foo\"bar")')

        em.move_to(5, 7)
        m_ec.assert_called_with('MoveCursor(4, 6)')

        em.send_pf3()
        m_ec.assert_called_with('PF(3)')

        em.send_pf4()
        m_ec.assert_called_with('PF(4)')

        em.send_pf5()
        m_ec.assert_called_with('PF(5)')

        em.send_pf6()
        m_ec.assert_called_with('PF(6)')

        m_ec.reset_mock()
        em.send_string('foobar', 5, 7)
        eq_(m_ec.call_args_list, [
            mock.call('MoveCursor(4, 6)'),
            mock.call('String("foobar")'),
        ])

    @mock.patch('py3270.EmulatorBase.connect')
    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_reconnect(self, m_ec, m_connect):
        em =  MEmulator()
        em.last_host = 'foo'
        em.reconnect()
        m_ec.assert_called_once_with('Disconnect')
        eq_(m_connect.call_args_list, [
            # call from reconnect()
            mock.call('foo'),
        ])

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_fill_field(self, m_ec):
        em =  MEmulator()

        em.fill_field(7, 9, 'foobar', 6)
        eq_(m_ec.call_args_list, [
            mock.call('MoveCursor(6, 8)'),
            mock.call('DeleteField'),
            mock.call('String("foobar")'),
        ])
        m_ec.reset_mock()

        em.fill_field(None, None, 'foobar', 6)
        eq_(m_ec.call_args_list, [
            mock.call('DeleteField'),
            mock.call('String("foobar")'),
        ])
        m_ec.reset_mock()

        em.fill_field(1, None, 'foobar', 6)
        eq_(m_ec.call_args_list, [
            mock.call('DeleteField'),
            mock.call('String("foobar")'),
        ])

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_string_get(self, m_ec):
        em =  MEmulator()
        m_ec.return_value.data = ['foobar']
        result = em.string_get(7,9,5)
        eq_(result, 'foobar')
        m_ec.assert_called_with('Ascii(6,8,5)')

    @raises(AssertionError)
    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_string_get_too_much_data(self, m_ec):
        em =  MEmulator()
        m_ec.return_value.data = ['foobar', 'baz']
        em.string_get(7,9,5)

    @mock.patch('py3270.EmulatorBase.string_get')
    def test_string_found(self, m_string_get):
        em =  MEmulator()
        m_string_get.return_value = 'foobar'

        assert em.string_found(7,9,'foobar')
        m_string_get.assert_called_once_with(7, 9, 6)

        assert not em.string_found(7,9,'baz')

    @raises(FieldTruncateError, 'length limit 5, but got "foobar"')
    def test_fill_field_length_error(self):
        em =  MEmulator()
        em.fill_field(1, 1, 'foobar', 5)

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_wait_for_field(self, m_ec):
        em =  MEmulator()
        em.status.keyboard = 'U'
        em.wait_for_field()

        m_ec.assert_called_once_with('Wait(3, InputField)')

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_wait_for_field_custom_timeout(self, m_ec):
        em =  MEmulator(timeout=5)
        em.status.keyboard = 'U'
        em.wait_for_field()

        m_ec.assert_called_once_with('Wait(5, InputField)')

    @raises(KeyboardStateError, 'keyboard not unlocked, state was: E')
    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_wait_for_field_exception(self, m_ec):
        em =  MEmulator()
        em.status.keyboard = 'E'
        em.wait_for_field()

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_not_is_connected(self, m_ec):
        em =  MEmulator()
        def assign_status(*args, **kwargs):
            em.status.connection_state = 'N'
        m_ec.side_effect = assign_status
        assert not em.is_connected()
        m_ec.assert_called_once_with('ignore')

    @mock.patch('py3270.EmulatorBase.exec_command')
    def test_is_connected(self, m_ec):
        em =  MEmulator()
        def assign_status(*args, **kwargs):
            em.status.connection_state = 'C(192.168.1.1)'
        m_ec.side_effect = assign_status
        assert em.is_connected()
        m_ec.assert_called_once_with('ignore')

class TestCommand(object):

    def test_defaults(self):
        cmd = MCommand()
        eq_(cmd.cmdstr, 'testcmd')
        eq_(cmd.status_line, None)
        eq_(cmd.data, [])

    def test_stdin(self):
        cmd = MCommand()
        cmd.execute()
        cmd.sp.stdin.write.assert_called_once_with('testcmd\n')

    def test_data(self):
        data = 'data: foo\n'
        data += 'data: bar\n'
        cmd = MCommand(data)
        cmd.execute()
        eq_(cmd.data, ['foo', 'bar'])

    def test_data_windows_line_endings(self):
        data = 'data: foo\r\n'
        data += 'data: bar\r\n'
        cmd = MCommand(data)
        cmd.execute()
        eq_(cmd.data, ['foo', 'bar'])

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
        cmd = MCommand(result='', cmdstr='Quit')
        # running without exception is sufficient for this test
        cmd.execute()

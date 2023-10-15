#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
from unittest import mock

from pytest import raises

from base import ExamApp, MCommand
from py3270 import CommandError


class TestCommand(object):
    def test_defaults(self):
        cmd = MCommand()
        assert cmd.cmdstr == b"testcmd"
        assert cmd.status_line is None
        assert cmd.data == []

    @mock.patch.object(ExamApp, "write")
    def test_stdin(self, m_write):
        cmd = MCommand()
        cmd.execute()
        cmd.app.write.assert_called_once_with(b"testcmd\n")

    def test_data(self):
        data = "data: foo\n"
        data += "data: bar\n"
        cmd = MCommand(data)
        cmd.execute()
        assert cmd.data == [b"foo", b"bar"]

    def test_data_windows_line_endings(self):
        data = "data: foo\r\n"
        data += "data: bar\r\n"
        cmd = MCommand(data)
        cmd.execute()
        assert cmd.data == [b"foo", b"bar"]

    def test_error_response(self):
        data = "data: some kind \n"
        data += "data: of error\n"
        cmd = MCommand(data, result="error")
        with raises(CommandError, match="some kind of error"):
            cmd.execute()

    def test_error_response_no_data(self):
        cmd = MCommand(result="error")
        with raises(CommandError, match="[no error message]"):
            cmd.execute()

    def test_unexpected_result(self):
        cmd = MCommand(result="foobar")
        with raises(
            ValueError, match=re.escape('expected "ok" or "error" result, but received: foobar')
        ):
            cmd.execute()

    def test_blank_result(self):
        cmd = MCommand(result="")
        with raises(
            ValueError, match=re.escape('expected "ok" or "error" result, but received: ')
        ):
            cmd.execute()

    def test_blank_result_with_quit(self):
        cmd = MCommand(result="", cmdstr=b"Quit")
        # running without exception is sufficient for this test
        cmd.execute()

#!/usr/bin/python3
# -*- coding: utf-8 -*-

from unittest import mock

import pytest

from base import MEmulator
from py3270 import (
    Emulator,
    EmulatorBase,
    FieldTruncateError,
    KeyboardStateError,
    TerminatedError,
)


class TestEmulator(object):
    def test_emulatorbase_exception(self):
        with pytest.raises(
            Exception, message="EmulatorBase has been replaced by Emulator."
        ):
            EmulatorBase()

    @mock.patch("py3270.Emulator.exec_command")
    def test_connect(self, m_ec):
        em = MEmulator.mock()
        assert em.last_host is None
        em.connect("localhost")
        assert em.last_host == "localhost"
        m_ec.assert_called_once_with(b"Connect(localhost)")

    @mock.patch("py3270.Emulator.exec_command")
    def test_terminate(self, m_ec):
        em = MEmulator.mock()
        em.terminate()
        m_ec.assert_called_once_with(b"Quit")
        assert em.is_terminated

    @mock.patch("py3270.Command")
    def test_command_after_terminate(self, m_cmd):
        em = MEmulator.mock()
        em.terminate()
        with pytest.raises(TerminatedError, message="Expecting TerminatedError"):
            em.connect("localhost")

    @mock.patch("py3270.Emulator.exec_command")
    def test_exec_methods(self, m_ec):
        em = MEmulator.mock()

        em.send_enter()
        m_ec.assert_called_with(b"Enter")

        em.send_string('foo"bar')
        m_ec.assert_called_with(b'String("foo"bar")')

        em.move_to(5, 7)
        m_ec.assert_called_with(b"MoveCursor(4, 6)")

        em.send_pf3()
        m_ec.assert_called_with(b"PF(3)")

        em.send_pf4()
        m_ec.assert_called_with(b"PF(4)")

        em.send_pf5()
        m_ec.assert_called_with(b"PF(5)")

        em.send_pf6()
        m_ec.assert_called_with(b"PF(6)")

        m_ec.reset_mock()
        em.send_string("foobar", 5, 7)
        assert m_ec.call_args_list == [
            mock.call(b"MoveCursor(4, 6)"),
            mock.call(b'String("foobar")'),
        ]

    @mock.patch("py3270.Emulator.connect")
    @mock.patch("py3270.Emulator.exec_command")
    def test_reconnect(self, m_ec, m_connect):
        em = MEmulator.mock()
        em.last_host = "foo"
        em.reconnect()
        assert m_ec.call_args_list[0] == mock.call(b"Disconnect")
        assert m_connect.call_args_list == [
            # call from reconnect()
            mock.call("foo")
        ]

    @mock.patch("py3270.Emulator.exec_command")
    def test_fill_field(self, m_ec):
        em = MEmulator.mock()

        em.fill_field(7, 9, "foobar", 6)
        assert m_ec.call_args_list == [
            mock.call(b"MoveCursor(6, 8)"),
            mock.call(b"DeleteField"),
            mock.call(b'String("foobar")'),
        ]
        m_ec.reset_mock()

        em.fill_field(None, None, "foobar", 6)
        assert m_ec.call_args_list == [
            mock.call(b"DeleteField"),
            mock.call(b'String("foobar")'),
        ]
        m_ec.reset_mock()

        em.fill_field(1, None, "foobar", 6)
        assert m_ec.call_args_list == [
            mock.call(b"DeleteField"),
            mock.call(b'String("foobar")'),
        ]

    @mock.patch("py3270.Emulator.exec_command")
    def test_string_get(self, m_ec):
        em = MEmulator.mock()
        m_ec.return_value.data = [b"foobar"]
        result = em.string_get(7, 9, 5)
        assert result == "foobar"
        m_ec.assert_called_with(b"Ascii(6,8,5)")
        em.terminate()

    @mock.patch("py3270.Emulator.exec_command")
    def test_string_get_too_much_data(self, m_ec):
        em = MEmulator.mock()
        m_ec.return_value.data = ["foobar", "baz"]
        with pytest.raises(AssertionError, message="Expecting AssertionError"):
            em.string_get(7, 9, 5)

    @mock.patch("py3270.Emulator.string_get")
    def test_string_found(self, m_string_get):
        em = MEmulator.mock()
        m_string_get.return_value = "foobar"

        assert em.string_found(7, 9, "foobar")
        m_string_get.assert_called_once_with(7, 9, 6)

        assert not em.string_found(7, 9, "baz")

    @mock.patch("py3270.Emulator.exec_command")
    def test_wait_for_field(self, m_ec):
        em = MEmulator.mock(timeout=3)
        em.status.keyboard = b"U"
        em.wait_for_field()

        m_ec.assert_called_once_with(b"Wait(3, InputField)")

    @mock.patch("py3270.Emulator.exec_command")
    def test_wait_for_field_custom_timeout(self, m_ec):
        em = MEmulator.mock(timeout=5)
        em.status.keyboard = b"U"
        em.wait_for_field()

        m_ec.assert_called_once_with(b"Wait(5, InputField)")

    @mock.patch("py3270.Emulator.exec_command")
    def test_wait_for_field_exception(self, m_ec):
        em = MEmulator.mock()
        em.status.keyboard = b"E"
        with pytest.raises(
            KeyboardStateError, message="keyboard not unlocked, state was: E"
        ):
            em.wait_for_field()

    @mock.patch("py3270.Emulator.exec_command")
    def test_not_is_connected(self, m_ec):
        em = MEmulator.mock()

        def assign_status(*args, **kwargs):
            em.status.connection_state = b"N"

        m_ec.side_effect = assign_status
        assert not em.is_connected()
        m_ec.assert_called_once_with(b"Query(ConnectionState)")

    @mock.patch("py3270.Emulator.exec_command")
    def test_is_connected(self, m_ec):
        em = MEmulator.mock()

        def assign_status(*args, **kwargs):
            em.status.connection_state = b"C(192.168.1.1)"

        m_ec.side_effect = assign_status
        assert em.is_connected()
        m_ec.assert_called_once_with(b"Query(ConnectionState)")

    def test_fill_field_length_error(self):
        em = MEmulator.mock()
        with pytest.raises(
            FieldTruncateError, message='length limit 5, but got "foobar"'
        ):
            em.fill_field(1, 1, "foobar", 5)

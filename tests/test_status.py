#!/usr/bin/python3
# -*- coding: utf-8 -*-

from py3270 import Status


class TestStatus(object):
    def test_empty(self):
        s = Status(None)
        assert s.as_string == ""
        assert s.keyboard == None

    def test_split(self):
        statstr = b"U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082"
        s = Status(statstr)
        assert s.as_string == statstr.decode("ascii")
        assert s.keyboard == b"U"

    def test_str_magic(self):
        statstr = b"U F U C(192.85.72.197) I 4 24 80 16 22 0x0 0.082"
        s = Status(statstr)
        assert str(s) == "STATUS: " + statstr.decode("ascii")

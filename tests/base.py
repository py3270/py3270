#!/usr/bin/python3
# -*- coding: utf-8 -*-

from io import BytesIO

from py3270 import Emulator, Command

class MEmulator(object):
    @classmethod
    def mock(cls, timeout=30):
        return Emulator(timeout=timeout, app=ExamApp())

class MCommand(Command):
    def __init__(self, data="", result="ok", cmdstr=b"testcmd"):
        Command.__init__(self, ExamApp(data, result), cmdstr)        

class ExamApp(object):
    """ An object with an interface like ExecutableApp used for testing """

    def __init__(self, data="", result="ok"):
        self.stdin = BytesIO()

        response = data
        response += "" * 12 + "\n"
        response += result + "\n"
        self.stdout = BytesIO(response.encode("ascii"))

    def connect(self, host):
        return False

    def close(self):
        self.stdin.close()

    def write(self, data):
        self.stdin.write(data)
        self.stdin.flush()

    def readline(self):
        return self.stdout.readline()

#####################################################################################
#
#  Copyright (C) Tavendo GmbH
#
#  Unless a separate license agreement exists between you and Tavendo GmbH (e.g. you
#  have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU Affero General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  See the GNU Affero General Public License Version 3 for more details.
#
#  You should have received a copy of the GNU Affero General Public license along
#  with this program. If not, see <http://www.gnu.org/licenses/agpl-3.0.en.html>.
#
#####################################################################################

from __future__ import absolute_import, division, print_function

from six import StringIO as NativeStringIO

from twisted.trial import unittest
from twisted.internet.selectreactor import SelectReactor

from crossbar.controller import cli
from crossbar import _logging

from weakref import WeakKeyDictionary

import os
import sys
import platform
import twisted


class CLITestBase(unittest.TestCase):

    def setUp(self):

        self._subprocess_timeout = 15

        if platform.python_implementation() == 'PyPy':
            self._subprocess_timeout = 30

        self.stderr = NativeStringIO()
        self.stdout = NativeStringIO()

        self.patch(_logging, "_stderr", self.stderr)
        self.patch(_logging, "_stdout", self.stdout)
        self.patch(_logging, "_loggers", WeakKeyDictionary())
        self.patch(_logging, "_loglevel", "info")

    def tearDown(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class VersionTests(CLITestBase):

    def test_basic(self):
        """
        Just running `crossbar version` gets us the versions.
        """
        reactor = SelectReactor()

        cli.run("crossbar",
                ["version"],
                reactor=reactor)

        self.assertIn("Crossbar.io", self.stdout.getvalue())
        self.assertIn(
            ("Twisted          : \x1b[33m\x1b[1m" + twisted.version.short() + "-SelectReactor"),
            self.stdout.getvalue())

    def test_debug(self):
        """
        Running `crossbar version` will give us the versions, plus the
        locations of some of them.
        """
        reactor = SelectReactor()

        cli.run("crossbar",
                ["version", "--loglevel=debug"],
                reactor=reactor)

        self.assertIn("Crossbar.io", self.stdout.getvalue())
        self.assertIn(
            ("Twisted          : \x1b[33m\x1b[1m" + twisted.version.short() + "-SelectReactor"),
            self.stdout.getvalue())
        self.assertIn(
            ("[twisted.internet.selectreactor.SelectReactor]"),
            self.stdout.getvalue())


class StartTests(CLITestBase):

    def setUp(self):

        CLITestBase.setUp(self)

        # Set up the configuration directories
        self.cbdir = os.path.abspath(self.mktemp())
        os.mkdir(self.cbdir)
        self.config = os.path.abspath(os.path.join(self.cbdir, "config.json"))

    def test_start(self):
        """
        A basic start, that doesn't actually enter the reactor.
        """
        with open(self.config, "w") as f:
            f.write("""{"controller": {}}""")

        reactor = SelectReactor()
        reactor.run = lambda: False

        cli.run("crossbar",
                ["start", "--cbdir={}".format(self.cbdir),
                 "--logformat=syslogd"],
                reactor=reactor)

        self.assertIn("Entering reactor event loop", self.stdout.getvalue())

    def test_configValidationFailure(self):
        """
        Running `crossbar start` with an invalid config will print a warning.
        """
        with open(self.config, "w") as f:
            f.write("")

        reactor = SelectReactor()

        with self.assertRaises(SystemExit) as e:
            cli.run("crossbar",
                    ["start", "--cbdir={}".format(self.cbdir),
                     "--logformat=syslogd"],
                    reactor=reactor)

        # Exit with code 1
        self.assertEqual(e.exception.args[0], 1)

        # The proper warning should be emitted
        self.assertIn("*** Configuration validation failed ***",
                      self.stderr.getvalue())
        self.assertIn(("configuration file does not seem to be proper JSON "),
                      self.stderr.getvalue())

    def test_fileLogging(self):
        """
        Running `crossbar start --logtofile` will log to cbdir/node.log.
        """
        with open(self.config, "w") as f:
            f.write("""{"controller": {}}""")

        reactor = SelectReactor()
        reactor.run = lambda: None

        cli.run("crossbar",
                ["start", "--cbdir={}".format(self.cbdir), "--logtofile"],
                reactor=reactor)

        with open(os.path.join(self.cbdir, "node.log"), "r") as f:
            logFile = f.read()

        self.assertIn("Entering reactor event loop", logFile)
        self.assertEqual("", self.stderr.getvalue())
        self.assertEqual("", self.stdout.getvalue())

    def test_stalePID(self):

        with open(self.config, "w") as f:
            f.write("""{"controller": {}}""")

        with open(os.path.join(self.cbdir, "node.pid"), "w") as f:
            f.write("""{"pid": 9999999}""")

        reactor = SelectReactor()
        reactor.run = lambda: None

        cli.run("crossbar",
                ["start", "--cbdir={}".format(self.cbdir),
                 "--logformat=syslogd"],
                reactor=reactor)

        self.assertIn(
            ("Stale Crossbar.io PID file (pointing to non-existing process "
             "with PID {pid}) {fp} removed").format(
                 fp=os.path.abspath(os.path.join(self.cbdir, "node.pid")),
                 pid=9999999),
            self.stdout.getvalue())

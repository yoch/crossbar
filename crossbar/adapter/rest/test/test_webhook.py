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

from __future__ import absolute_import

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks

from crossbar._compat import native_string
from crossbar.adapter.rest import WebhookResource
from crossbar.adapter.rest.test import MockPublisherSession, renderResource


class WebhookTestCase(TestCase):
    """
    Unit tests for L{WebhookResource}.
    """
    @inlineCallbacks
    def test_basic(self):
        """
        A message, when a request has gone through to it, publishes a WAMP
        message on the configured topic.
        """
        session = MockPublisherSession(self)
        resource = WebhookResource({u"topic": u"com.test.webhook"}, session)

        request = yield renderResource(
            resource, b"/",
            method=b"POST",
            headers={b"Content-Type": []},
            body=b'{"foo": "has happened"}')

        self.assertEqual(len(session._published_messages), 1)
        self.assertEqual(
            {
                "body": '{"foo": "has happened"}',
                "headers": {
                    "Content-Type": [],
                    'Date': ['Tue, 01 Jan 2014 01:01:01 GMT'],
                    'Host': ['localhost:8080']
                }
            },
            session._published_messages[0]["args"][0])

        self.assertEqual(request.code, 202)
        self.assertEqual(native_string(request.getWrittenData()),
                         "OK")

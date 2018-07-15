# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from channels.exceptions import WebsocketCloseException

import json

class ClientError(Exception):
    def __init__(self, code):
        super(ClientError, self).__init__(code)
        self.code = code

    def send_to(self, channel):
        channel.send({
            "text": json.dumps({
                "action": "error",
                "message": self.code,
            }),
        })

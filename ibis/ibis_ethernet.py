#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Julian Metzler
# See the LICENSE file for the full license.

"""
Ethernet protocol wrapper
"""

import socket
from .ibis_utils import prepare_text

class EthernetWrapper(object):
    def __init__(self, host, port, timeout = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
    
    def send_message(self, text):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            sock.sendall(prepare_text(text))
        finally:
            sock.close()
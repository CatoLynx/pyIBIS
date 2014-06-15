# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Various convenience functions used internally in multiple places
"""

import json

def _receive_datagram(sock):
	# Receive and parse an incoming datagram (prefixed with its length)
	try:
		length = int(sock.recv(4))
		
		raw_data = ""
		read_length = 0
		while read_length < length:
			part = sock.recv(1024)
			raw_data += part
			read_length += len(part)
		
		datagram = json.loads(raw_data)
	except:
		return None
	return datagram

def _send_datagram(sock, data):
	# Build and send a datagram (prefixed with its length)
	raw_data = json.dumps(data)
	length = len(raw_data)
	datagram = "%04i%s" % (length, raw_data)
	sock.sendall(datagram)
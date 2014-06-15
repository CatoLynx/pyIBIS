#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Client for the client-server system
"""

import argparse
import re
import socket
import time

from .ibis_utils import _receive_datagram, _send_datagram

class Client(object):
	def __init__(self, host, port = 4242, timeout = 5.0):
		self.host = host
		self.port = port
		self.timeout = timeout
		self.socket = None
	
	def send_raw_message(self, message, expect_reply = True):
		"""
		Send a message to the server
		"""
		
		reply = None
		
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(self.timeout)
			sock.connect((self.host, self.port))
			_send_datagram(sock, message)
			
			if expect_reply:
				reply = _receive_datagram(sock)
		finally:
			sock.close()
		
		return reply
	
	def set_enabled(self, address, value):
		"""
		Enable or disable a display
		"""
		
		return self.send_raw_message({'address': address, 'enable': value})
	
	def set_stop_indicator(self, address, state):
		"""
		Enable or disable a stop indicator
		"""
		
		return self.send_raw_message({'address': address, 'stop_indicator': state})
	
	def set_message(self, address, message, priority = 0, client = None):
		"""
		Set the message for a display
		"""
		
		message = {
			'address': address,
			'message': message,
			'priority': priority,
		}
		
		if client:
			message['client'] = client
		
		return self.send_raw_message(message)
	
	def make_text(self, text, duration = None):
		message = {'type': 'text', 'text': text}
		if duration:
			message['duration'] = duration
		
		return message
	
	def set_text(self, address, text, duration = None, priority = 0, client = None):
		"""
		Set a static text on a display
		"""
		
		return self.set_message(address, self.make_text(text, duration), priority, client)
	
	def make_time(self, format, duration = None):
		message = {'type': 'time', 'format': format}
		if duration:
			message['duration'] = duration
		
		return message
	
	def set_time(self, address, format, duration = None, priority = 0, client = None):
		"""
		Set a display to display the current time
		"""
		
		return self.set_message(address, self.make_time(format, duration), priority, client)
	
	def set_sequence(self, address, sequence, interval, priority = 0, client = None):
		"""
		Set a display to display a sequence of messages
		"""
		
		return self.set_message(address, {'type': 'sequence', 'messages': sequence, 'interval': interval}, priority, client)
	
	def get_current_text(self):
		"""
		Query the server for the text that is currently being displayed
		"""
		
		current = self.send_raw_message({'query': 'current_text'})
		current = dict([(int(key), value) for key, value in current.iteritems()])
		return current
	
	def get_buffer(self):
		"""
		Query the server for the text that is set to be displayed for each display
		"""
		
		buffer = self.send_raw_message({'query': 'buffer'})
		buffer = dict([(int(key), value) for key, value in buffer.iteritems()])
		return buffer
	
	def get_enabled(self):
		"""
		Query the server for the enabled states
		"""
		
		enabled = self.send_raw_message({'query': 'enabled'})
		enabled = dict([(int(key), value) for key, value in enabled.iteritems()])
		return enabled
	
	def get_stop_indicators(self):
		"""
		Query the server for the current state of the stop indicators
		"""
		
		indicators = self.send_raw_message({'query': 'stop_indicators'})
		indicators = dict([(int(key), value) for key, value in indicators.iteritems()])
		return indicators
	
	def get_all(self):
		"""
		Query the server for all available status information
		"""
		
		status = self.send_raw_message({'query': 'all'})
		for subsection, subdict in status.iteritems():
			subdict = dict([(int(key), value) for key, value in subdict.iteritems()])
			status[subsection] = subdict
		return status
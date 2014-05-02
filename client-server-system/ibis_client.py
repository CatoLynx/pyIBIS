#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Client for the client-server system
"""

import argparse
import json
import re
import socket
import time

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
			sock.sendall(json.dumps(message))
			if expect_reply:
				reply = json.loads(sock.recv(4096))
		finally:
			sock.close()
		return reply
	
	def set_enabled(self, value):
		"""
		Enable or disable the displays
		"""
		
		return self.send_raw_message({'enable': value})
	
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
		
		current = self.send_raw_message({'query': 'current'})
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
		Query the server for the enabled state
		"""
		
		enabled = self.send_raw_message({'query': 'enabled'})
		return enabled
	
	def get_stop_indicators(self):
		"""
		Query the server for the current state of the stop indicators
		"""
		
		indicators = self.send_raw_message({'query': 'stop_indicators'})
		indicators = dict([(int(key), value) for key, value in indicators.iteritems()])
		return indicators

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-host', '--host', type = str, default = "localhost")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	parser.add_argument('-d', '--display', type = int, choices = [0, 1, 2, 3])
	parser.add_argument('-t', '--type', choices = ['text', 'time', 'sequence'])
	parser.add_argument('-v', '--value', type = str)
	parser.add_argument('-pr', '--priority', type = int, default = 0)
	parser.add_argument('-c', '--client', type = str)
	parser.add_argument('-i', '--interval', type = float, default = 5.0)
	parser.add_argument('-s', '--state', choices = ['on', 'off', 'toggle'])
	parser.add_argument('-si', '--stop-indicator', choices = ['on', 'off', 'toggle'])
	args = parser.parse_args()
	
	client = Client(args.host, args.port)
	
	if args.state == 'on':
		client.set_enabled(True)
	elif args.state == 'off':
		client.set_enabled(False)
	elif args.state == 'toggle':
		client.set_enabled('toggle')
	
	if args.type == 'text':
		client.set_text(args.display, args.value, priority = args.priority, client = args.client)
	elif args.type == 'time':
		client.set_time(args.display, args.value, priority = args.priority, client = args.client)
	elif args.type == 'sequence':
		sequence = []
		items = args.value.split("|")
		for item in items:
			try:
				parts = item.split("~")
				duration = float(parts[-1])
				item = "~".join(parts[:-1])
			except:
				duration = None
			
			if re.match(r"^.*%[-a-zA-Z].*$", item):
				sequence.append(client.make_time(item, duration))
			else:
				sequence.append(client.make_text(item, duration))
		client.set_sequence(args.display, sequence, args.interval, priority = args.priority, client = args.client)
	
	if args.stop_indicator == 'on':
		client.set_stop_indicator(args.display, True)
	elif args.stop_indicator == 'off':
		client.set_stop_indicator(args.display, False)
	elif args.stop_indicator == 'toggle':
		client.set_stop_indicator(args.display, 'toggle')

if __name__ == "__main__":
	main()
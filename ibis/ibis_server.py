#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Server for the client-server system
"""

import argparse
import ibis
import json
import socket
import thread
import time

from .ibis_utils import _receive_datagram, _send_datagram

class Listener(object):
	def __init__(self, controller, port = 4245):
		self.controller = controller
		self.port = port
		self.running = False
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	def run(self):
		self.running = True
		
		# Open the network socket and listen
		self.socket.bind(('', self.port))
		print "Listening on port %i" % self.port
		self.socket.listen(1)
		
		try:
			while self.running:
				try:
					# Wait for someone to connect
					conn, addr = self.socket.accept()
					print "Accepted connection from %s on port %i" % addr
					
					# Load the datagram
					message = _receive_datagram(conn)
					
					if message is None:
						# We received an invalid datagram, just discard it
						continue
					
					success = True
					if 'enable' in message:
						try:
							if message['enable'] == 'toggle':
								state = not self.controller.get_enabled(int(message['address']))
							else:
								state = bool(message['enable'])
							
							success = self.controller.set_enabled(int(message['address']), state)
						except:
							success = False
						_send_datagram(conn, {'success': success})
					elif 'query' in message:
						if message['query'] == 'current_text':
							_send_datagram(conn, self.controller.current_text)
						elif message['query'] == 'buffer':
							_send_datagram(conn, self.controller.buffer)
						elif message['query'] == 'enabled':
							_send_datagram(conn, self.controller.enabled)
						elif message['query'] == 'stop_indicators':
							_send_datagram(conn, self.controller.stop_indicators)
						elif message['query'] == 'all':
							status = {
								'buffer': self.controller.buffer,
								'current_text': self.controller.current_text,
								'enabled': self.controller.enabled,
								'stop_indicators': self.controller.stop_indicators
							}
							_send_datagram(conn, status)
					elif 'stop_indicator' in message:
						try:
							if message['stop_indicator'] == 'toggle':
								state = not self.controller.stop_indicators[message['address']]
							else:
								state = bool(message['stop_indicator'])
							
							success = self.controller.set_stop_indicator(int(message['address']), state)
						except:
							success = False
						_send_datagram(conn, {'success': success})
					else:
						try:
							success = self.controller.set_message(message['address'], message['message'], priority = message.get('priority', 0), client = message.get('client', addr[0]))
						except:
							success = False
						_send_datagram(conn, {'success': success})
				except KeyboardInterrupt:
					self.quit()
		finally:
			self.socket.close()
	
	def quit(self):
		self.running = False

class Controller(object):
	DEBUG = False
	VERBOSE = True
	TIMEOUT = 120.0
	
	def __init__(self, master):
		self.master = master
		self.running = False
		
		self.buffer = {
			0: {
				'message': None,
				'priority': -1,
				'client': None,
				'current': -1,
				'last_refresh': 0.0,
				'last_update': 0.0
			},
			1: {
				'message': None,
				'priority': -1,
				'client': None,
				'current': -1,
				'last_refresh': 0.0,
				'last_update': 0.0
			},
			2: {
				'message': None,
				'priority': -1,
				'client': None,
				'current': -1,
				'last_refresh': 0.0,
				'last_update': 0.0
			},
			3: {
				'message': None,
				'priority': -1,
				'client': None,
				'current': -1,
				'last_refresh': 0.0,
				'last_update': 0.0
			}
		}
		
		self.enabled = {
			0: True,
			1: True, 
			2: True,
			3: True
		}
		
		self.current_text = {
			0: None,
			1: None,
			2: None,
			3: None
		}
		
		self.stop_indicators = {
			0: False,
			1: False,
			2: False,
			3: False
		}
		
		try:
			self.load_config()
		except:
			if self.VERBOSE:
				print "Failed to load configuration"
	
	def _reverse_prepare_text(self, message):
		def _do_replace(message):
			message = message.replace("{", u"ä")
			message = message.replace("|", u"ö")
			message = message.replace("}", u"ü")
			message = message.replace("~", u"ß")
			message = message.replace("[", u"Ä")
			message = message.replace("\\", u"Ö")
			message = message.replace("]", u"Ü")
			message = message.encode('utf-8')
			return message
		
		try:
			message = _do_replace(message)
		except UnicodeDecodeError:
			message = message.decode('utf-8')
			message = _do_replace(message)
		
		return message
	
	def save_config(self, filename = "ibis.json"):
		if self.VERBOSE:
			print "Saving configuration..."
		
		data = {
			'buffer': self.buffer,
			'current_text': self.current_text,
			'enabled': self.enabled,
			'stop_indicators': self.stop_indicators,
		}
		
		with open(filename, 'w') as f:
			f.write(json.dumps(data))
		
		if self.VERBOSE:
			print "Successfully saved configuration"
	
	def load_config(self, filename = "ibis.json"):
		if self.VERBOSE:
			print "Loading configuration..."
		
		with open(filename, 'r') as f:
			data = json.loads(f.read())
		
		for address, entry in data['buffer'].iteritems():
			if entry['message']:
				self.set_message(int(address), entry['message'], priority = entry.get('priority', 0), client = entry.get('client', None))
		
		for address, state in data['stop_indicators'].iteritems():
			self.set_stop_indicator(int(address), state)
		
		for address, state in data['enabled'].iteritems():
			self.set_enabled(int(address), state)
		
		if self.VERBOSE:
			print "Successfully loaded configuration"
	
	def set_stop_indicator(self, address, value):
		self.master.set_stop_indicator(address, value)
		self.stop_indicators[address] = value
		
		if self.VERBOSE:
			print "Stop indicator on display %i set to %s" % (address, str(value))
		
		self.save_config()
		return True
	
	def set_enabled(self, address, value):
		"""
		Enable or disable a display
		"""
		
		if address == -1:
			for i in range(4):
				self.set_enabled(i, value)
			return True
		
		self.enabled[address] = value
		
		if not self.enabled[address]:
			self.send_text(address, None) # This seems to fail quite often! Why?
		
		if self.VERBOSE:
			print "Power state of display %i changed to %s" % (address, str(value))
		
		self.save_config()
		return True
	
	def get_enabled(self, address):
		"""
		Return the enabled state for the given address and perform some logic
		in case we're dealing with address -1
		"""
		
		if address == -1:
			return self.enabled[0] and self.enabled[1] and self.enabled[2] and self.enabled[3]
		else:
			return self.enabled.get(address, False)
	
	def send_text(self, address, text):
		"""
		Send text to a display
		"""
		
		# Set the address on the multiplexer or send to all displays if address is -1
		if address == -1:
			for i in range(4):
				self.send_text(i, text)
			return
		elif address == 0:
			self.master.device.setDTR(0)
			self.master.device.setRTS(0)
		elif address == 1:
			self.master.device.setDTR(0)
			self.master.device.setRTS(1)
		elif address == 2:
			self.master.device.setDTR(1)
			self.master.device.setRTS(0)
		elif address == 3:
			self.master.device.setDTR(1)
			self.master.device.setRTS(1)
		
		# Truncate the text
		if text:
			text = text[:36]
		
		# Send the data
		self.master.send_next_stop__003c("" if text is None else text)
		if self.DEBUG:
			print address, text.encode('utf-8')
		
		# Save the current text
		self.current_text[address] = self._reverse_prepare_text(text).decode('utf-8') if text else None
	
	def set_message(self, address, message, priority = 0, client = None):
		"""
		Set the stuff to be displayed on a display, like a sequence of texts
		
		Message Examples
		
			Simple text
				{
					'type': 'text',
					'text': "Hello world"
				}
			
			Formatted time
				{
					'type': 'time',
					'format': "%d.%m.%Y %H:%M"
				}
			
			Two alternating texts with the same interval
				{
					'type': 'sequence',
					'messages': [
						{
							'type': 'time',
							'format': "%d.%m.%Y %H:%M"
						},
						{
							'type': 'text',
							'text': "SE50 Frankfurt"
						}
					],
					'interval': 5.0
				}
			
			Two alternating texts with different intervals
				{
					'type': 'sequence',
					'messages': [
						{
							'type': 'text',
							'text': "Next Stop",
							'duration': 2.0
						},
						{
							'type': 'text',
							'text': "Frankfurt",
							'duration': 5.0
						}
					],
					'interval': 5.0
				}
		
		Note: The 'interval' property of sequences is used for all messages that don't specify a duration of their own.
		"""
		
		def _filter_ascii(message):
			# Filter out everything that's not 7-bit ASCII
			if message['type'] == 'text':
				text = ""
				for char in message['text']:
					if ord(char) <= 127 or char in [u"ä", u"ö", u"ü", u"Ä", u"Ö", u"Ü", u"ß"]:
						text += char
				message['text'] = text
			elif message['type'] == 'time':
				text = ""
				for char in message['format']:
					if ord(char) <= 127 or char in [u"ä", u"ö", u"ü", u"Ä", u"Ö", u"Ü", u"ß"]:
						text += char
				message['format'] = text
			return message
		
		# Discard messages with a lower priority then the one in the buffer if not sent by the same client
		current_priority = self.buffer[address]['priority']
		current_client = self.buffer[address]['client']
		if priority < current_priority and client != current_client:
			if self.VERBOSE:
				print "Discarded message from %s for display %i (Priority was %i, current is %i set by %s)" % (client, address, priority, current_priority, current_client)
			return False
		
		if message['type'] == 'text':
			message = _filter_ascii(message)
		elif message['type'] == 'time':
			message = _filter_ascii(message)
		elif message['type'] == 'sequence':
			for index, msg in enumerate(message['messages']):
				message['messages'][index] = _filter_ascii(message['messages'][index])
		
		self.buffer[address]['message'] = message
		self.buffer[address]['priority'] = priority
		self.buffer[address]['client'] = client
		self.buffer[address]['current'] = -1
		self.buffer[address]['last_refresh'] = 0.0
		self.buffer[address]['last_update'] = 0.0
		
		if self.VERBOSE:
			print "Message on display %i set by %s with priority %i: %s" % (address, client, priority, str(message))
		
		self.save_config()
		
		return True
	
	def send_message(self, address, message):
		"""
		Send a single message of various types
		"""
		
		now = time.time()
		current_text = self.current_text[address]
		last_refresh = self.buffer[address]['last_refresh']
		last_update = self.buffer[address]['last_update']
		
		if message:
			if message['type'] == 'text':
				if current_text != message['text']:
					self.send_text(address, message['text'])
					self.buffer[address]['last_refresh'] = now
					self.buffer[address]['last_update'] = now
				elif last_refresh + self.TIMEOUT <= now:
					self.send_text(address, current_text)
					self.buffer[address]['last_refresh'] = now
			elif message['type'] == 'time':
				try:
					text = time.strftime(message['format'])
				except:
					text = time.strftime(message['format'].encode('utf-8'))
				if current_text != text:
					self.send_text(address, text)
					self.buffer[address]['last_refresh'] = now
					self.buffer[address]['last_update'] = now
				elif last_refresh + self.TIMEOUT <= now:
					self.send_text(address, current_text)
					self.buffer[address]['last_refresh'] = now
			elif message['type'] == 'sequence':
				default_interval = message['interval']
				messages = message['messages']
				current = self.buffer[address]['current']
				if current == -1 or current >= len(messages) - 1:
					next_message = 0
				else:
					next_message = current + 1
				duration = messages[current].get('duration', None)
				if duration is None:
					duration = default_interval
				if last_update + duration <= now:
					self.buffer[address]['current'] = next_message
					self.send_message(address, messages[next_message])
				elif last_refresh + self.TIMEOUT <= now:
					self.send_text(address, current_text)
					self.buffer[address]['last_refresh'] = now
		else:
			if current_text is not None:
				self.send_text(address, None)
				self.buffer[address]['last_update'] = now
	
	def selftest(self):
		self.send_text(-1, None)
		time.sleep(2)
		self.send_text(-1, "IBIS Server")
		time.sleep(2)
		self.send_text(-1, "by Mezgrman")
		time.sleep(2)
		self.send_text(-1, "www.mezgrman.de")
		time.sleep(2)
		for i in range(4):
			self.send_text(i, "Display %i" % i)
		time.sleep(5)
		"""self.send_text(-1, "0" * 16)
		time.sleep(1)
		self.send_text(-1, "1" * 16)
		time.sleep(1)
		self.send_text(-1, "2" * 16)
		time.sleep(1)
		self.send_text(-1, "3" * 16)
		time.sleep(1)
		self.send_text(-1, "4" * 16)
		time.sleep(1)
		self.send_text(-1, "5" * 16)
		time.sleep(1)
		self.send_text(-1, "6" * 16)
		time.sleep(1)
		self.send_text(-1, "7" * 16)
		time.sleep(1)
		self.send_text(-1, "8" * 16)
		time.sleep(1)
		self.send_text(-1, "9" * 16)
		time.sleep(1)"""
		self.send_text(-1, None)
	
	def process_buffer(self):
		"""
		Periodically check what's in the buffer and update the displays if necessary
		"""
		
		while self.running:
			for address in range(4):
				if self.enabled[address]:
					data = self.buffer[address]
					message = data['message']
					self.send_message(address, message)
			time.sleep(0.1)
	
	def run(self):
		self.running = True
		self.process_buffer()
	
	def quit(self):
		self.save_config()
		self.running = False

class Server(object):
	def __init__(self, serial_port, port = 4242, timeout = 120, gpio_pinmap = {}, verbose = False, debug = False, selftest = False):
		self.master = ibis.IBISMaster(serial_port, gpio_pinmap = gpio_pinmap)
		self.controller = Controller(self.master)
		self.controller.TIMEOUT = timeout
		self.controller.VERBOSE = verbose
		self.controller.DEBUG = debug
		
		if selftest:
			self.controller.selftest()
		
		self.listener = Listener(self.controller, port = port)
	
	def run(self):
		thread.start_new_thread(self.controller.run, ())
		self.listener.run()
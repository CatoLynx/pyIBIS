# Copyright (C) 2014 Julian Metzler
# -*- coding: utf-8 -*-
# See the LICENSE file for the full license.

"""
Main protocol library
"""

import serial
import time

# Try importing the GPIO lib in case we're on a Raspberry Pi (to control the stop indicators)
try:
	import wiringpi
	HAVE_GPIO = True
except ImportError:
	HAVE_GPIO = False

"""
Example GPIO pinmap:

{
	0: 28,
	1: 29,
	2: 31,
	3: 30
}

(Display ID -> GPIO pin)
"""

class IBISMaster(object):
	def __init__(self, port, gpio_pinmap = {}):
		self.port = port
		self.gpio_pinmap = gpio_pinmap
		
		if HAVE_GPIO:
			self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
			
			for pin in self.gpio_pinmap.values():
				self.gpio.pinMode(pin, self.gpio.OUTPUT)
		
		self.device = serial.serial_for_url(
			self.port,
			baudrate = 1200,
			bytesize = serial.SEVENBITS,
			parity = serial.PARITY_EVEN,
			stopbits = serial.STOPBITS_TWO
		)
	
	def hash(self, message):
		check_byte = 0x7F
		
		for char in message:
			byte = ord(char)
			check_byte = check_byte ^ byte
		
		message += chr(check_byte)
		return message
	
	def prepare_text(self, message):
		def _do_replace(message):
			message = message.replace(u"ä", "{")
			message = message.replace(u"ö", "|")
			message = message.replace(u"ü", "}")
			message = message.replace(u"ß", "~")
			message = message.replace(u"Ä", "[")
			message = message.replace(u"Ö", "\\")
			message = message.replace(u"Ü", "]")
			message = message.encode('utf-8')
			return message
		
		try:
			message = _do_replace(message)
		except UnicodeDecodeError:
			message = message.decode('utf-8')
			message = _do_replace(message)
		
		return message
	
	def set_stop_indicator(self, address, value):
		if not HAVE_GPIO:
			return False
		
		pin = self.gpio_pinmap.get(address, None)
		if pin is None:
			return False
		
		self.gpio.digitalWrite(pin, bool(value))
	
	def send_raw(self, data):
		#print repr(data)
		hex_data = ""
		for byte in data:
			hex_data += "<%s>" % hex(ord(byte))[2:].upper().rjust(2, "0")
		#print hex_data
		length = self.device.write(data)
		time.sleep(length * (12 / 1200.0))
		return length
	
	def send_message(self, message):
		message = self.hash(message + "\r")
		return self.send_raw(message)
	
	def send_line_number(self, line_number):
		message = "l%03i" % line_number
		return self.send_message(message)
	
	def send_special_character(self, character):
		message = "lE%02i" % character
		return self.send_message(message)
	
	def send_target_number(self, target_number):
		message = "z%03i" % target_number
		return self.send_message(message)
	
	def send_time(self, hours, minutes):
		message = "u%02i%02i" % (hours, minutes)
		return self.send_message(message)
	
	def send_date(self, day, month, year):
		message = "d%02i%02i%i" % (day, month, year)
		return self.send_message(message)
	
	def send_target_text__003a(self, text):
		text = self.prepare_text(text)
		blocks, remainder = divmod(len(text), 16)
		
		if remainder:
			blocks += 1
			text += " " * (16 - remainder)
		
		message = "zA%i%s" % (blocks, text.upper())
		return self.send_message(message)
	
	def send_target_text__021(self, text, id):
		text = self.prepare_text(text)
		blocks, remainder = divmod(len(text), 16)
		
		if remainder:
			blocks += 1
			text += " " * (16 - remainder)
		
		message = "aA%i%i%s" % (id, blocks, text.upper())
		return self.send_message(message)
	
	def send_next_stop__009(self, next_stop, length = 16):
		next_stop = self.prepare_text(next_stop)
		message = "v%s" % next_stop.upper().ljust(length)
		return self.send_message(message)
	
	def send_next_stop__003c(self, next_stop):
		next_stop = self.prepare_text(next_stop)
		blocks, remainder = divmod(len(next_stop), 4)
		
		if remainder:
			blocks += 1
			next_stop += " " * (4 - remainder)
		
		message = "zI%i%s" % (blocks, next_stop)
		return self.send_message(message)
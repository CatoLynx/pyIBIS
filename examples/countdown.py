#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display a countdown
"""

import argparse
import datetime
import ibis
import time

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-host', '--host', type = str, default = "localhost")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	parser.add_argument('-d', '--display', type = int, choices = (0, 1, 2, 3))
	parser.add_argument('-pr', '--priority', type = int, default = 0)
	parser.add_argument('-cl', '--client', type = str, default = "countdown.py")
	parser.add_argument('-f', '--format', type = str, default = "%(what)s in %(days)id %(hours)02i:%(minutes)02i:%(seconds)02i",
		help = "The format to display the countdown in. Variables: %%(what)s, %%(days)i, %%(hours)02i, %%(minutes)02i, %%(seconds)02i")
	parser.add_argument('-w', '--what', type = str, default = "Event")
	parser.add_argument('-t', '--target', type = str, required = True, help = "The target to count down to. Format: %%d.%%m.%%Y %%H:%%M:%%S")
	parser.add_argument('-e', '--end-text', type = str, default = "COUNTDOWN OVER!")
	args = parser.parse_args()
	
	client = ibis.Client(args.host, args.port)
	target = datetime.datetime.strptime(args.target, "%d.%m.%Y %H:%M:%S")
	
	while True:
		now = datetime.datetime.now()
		delta = target - now
		seconds = delta.total_seconds()
		
		if seconds < 0:
			break
		
		minutes, seconds = divmod(seconds, 60)
		hours, minutes = divmod(minutes, 60)
		days, hours = divmod(hours, 24)
		
		if "seconds" in args.format:
			interval = 1
		else:
			interval = 60
		
		text = args.format % {'what': args.what, 'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}
		client.set_text(args.display, text, priority = args.priority, client = args.client)
		time.sleep(interval)
	
	client.set_stop_indicator(args.display, True)
	client.set_text(args.display, args.end_text, priority = args.priority, client = args.client)

if __name__ == "__main__":
	main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Example command-line script that uses the IBIS client
"""

import argparse
import ibis

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
	
	client = ibis.Client(args.host, args.port)
	
	if args.state == 'on':
		if args.display:
			client.set_enabled(args.display, True)
		else:
			client.set_enabled(-1, True)
	elif args.state == 'off':
		if args.display:
			client.set_enabled(args.display, False)
		else:
			client.set_enabled(-1, False)
	elif args.state == 'toggle':
		if args.display:
			client.set_enabled(args.display, 'toggle')
		else:
			client.set_enabled(-1, 'toggle')
	
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
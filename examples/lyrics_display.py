#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Setting:
- Music event
- You are in charge of the music
- You have an IBIS display on the stage
- You want it to display the lyrics to the current song

That's what this script is for.
"""

import argparse
import ibis
import time

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--device', type = str, default = "/dev/ttyUSB0", help = "The serial device to use for IBIS communication")
	parser.add_argument('-f', '--file', type = str, help = "The filename of a text file to load entries from.")
	parser.add_argument('-s', '--server', type = str, help = "The host for server communication")
	parser.add_argument('-p', '--port', type = int, default = 1337, help = "The port for server communication")
	args = parser.parse_args()
	
	with open(args.file, 'r') as f:
		lines = [entry.rstrip("\n") for entry in f.readlines()]
	
	if args.server:
		wrapper = ibis.EthernetWrapper(args.server, args.port)
	else:
		master = ibis.IBISMaster(args.device)
	
	current_line = 0
	
	for line in lines:
		raw_input("Next line: %s" % line)
		if args.server:
			wrapper.send_message(line)
		else:
			master.send_next_stop__003c(line)
	
	print "End of lyrics file. Exiting."

if __name__ == "__main__":
	main()
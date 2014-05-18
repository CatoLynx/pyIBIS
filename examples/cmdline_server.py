#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Example command-line script that uses the IBIS server
"""

import argparse
import ibis

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', action = 'store_true')
	parser.add_argument('-d', '--debug', action = 'store_true')
	parser.add_argument('-s', '--selftest', action = 'store_true')
	parser.add_argument('-t', '--timeout', type = int, default = 120)
	parser.add_argument('-sp', '--serial-port', type = str, default = "/dev/ttyUSB0")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	args = parser.parse_args()
	
	gpio_pinmap = {
		0: 28,
		1: 29,
		2: 31,
		3: 30
	}
	
	server = ibis.Server(args.serial_port, port = args.port, timeout = args.timeout, gpio_pinmap = gpio_pinmap, verbose = args.verbose, debug = args.debug, selftest = args.selftest)
	server.run()

if __name__ == "__main__":
	main()
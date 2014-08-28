#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display "next stop" information with a random German train station
"""

import argparse
import ibis
import os
import random
import re
import sqlite3
import time

def tts_modify(stop):
	tts_stop = re.sub(r"([\s\(])b", r"\1bei", stop)
	tts_stop = re.sub(r"([\s\(])Kr", r"\1Kreis", tts_stop)
	tts_stop = tts_stop.replace(u"Hbf", u"Hauptbahnhof")
	tts_stop = tts_stop.replace(u"Pbf", u"Personenbahnhof")
	tts_stop = tts_stop.replace(u"Gbf", u"Güterbahnhof")
	tts_stop = tts_stop.replace(u"Rbf", u"Rangierbahnhof")
	return tts_stop

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-host', '--host', type = str, default = "localhost")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	parser.add_argument('-d', '--display', type = int, choices = (0, 1, 2, 3))
	parser.add_argument('-pr', '--priority', type = int, default = 0)
	parser.add_argument('-cl', '--client', type = str, default = "random_train.py")
	parser.add_argument('-si', '--sequence-interval', type = int, default = 5)
	parser.add_argument('-db', '--database', type = str, default = "db_stations.db")
	parser.add_argument('-j', '--jingle', type = str, default = "station_jingle.wav")
	parser.add_argument('-ij', '--info-jingle', type = str, default = "info_jingle.wav")
	parser.add_argument('-sj', '--stop-jingle', type = str, default = "stop_jingle.wav")
	parser.add_argument('-q', '--quiet', action = 'store_true')
	args = parser.parse_args()
	
	client = ibis.Client(args.host, args.port)
	
	db = sqlite3.connect(args.database)
	cur = db.cursor()
	cur.execute("SELECT * FROM `stations`")
	stations = [row[1] for row in cur.fetchall()]
	
	while True:
		num_stops = random.randint(3, 20)
		stops = random.sample(stations, num_stops)
		target = stops[-1]
		train_type = random.choice(["RB", "RE", "S"])
		train_number = random.randint(1, 99)
		has_stopped = True
		
		print "%s%i %s" % (train_type, train_number, target)
		
		for i in range(num_stops):
			stop = stops[i]
			direction = random.choice(["links", "rechts"])
			will_stop = random.choice([True, False])
			cycle_interval = random.uniform(10, 30)
			
			if direction == "links":
				if will_stop:
					print "    [S] <", stop
				else:
					print "        <", stop
			elif direction == "rechts":
				if will_stop:
					print "    [S] >", stop
				else:
					print "        >", stop
			
			client.set_stop_indicator(args.display, False)
			
			idle_sequence = []
			idle_sequence.append(client.make_text("%s%i %s" % (train_type, train_number, target)))
			idle_sequence.append(client.make_time("%d.%m.%Y %H:%M"))
			client.set_sequence(args.display, idle_sequence, args.sequence_interval, priority = args.priority, client = args.client)
			
			if not args.quiet and has_stopped:
				os.popen("aplay -q %s" % args.info_jingle)
				os.popen((u"espeak -v mb/mb-de5 -s 40 '%s %i nach %s'" % (train_type, train_number, tts_modify(target).replace("'", "\\'"))).encode('utf-8'))
			
			wait_time = random.uniform(5, 30)
			time.sleep(wait_time)
			
			sequence = []
			sequence.append(client.make_text("Nächster Halt:"))
			sequence.append(client.make_text(stop))
			sequence.append(client.make_text("Ausstieg %s" % direction))
			client.set_sequence(args.display, sequence, args.sequence_interval, priority = args.priority, client = args.client)
			
			if not args.quiet:
				os.popen("aplay -q %s" % args.jingle)
				if i == num_stops - 1:
					os.popen((u"espeak -v mb/mb-de5 -s 40 'Nähxter Halt: %s. Endstation. Bitte aussteigen. Ausstieg in Fahrtrichtung %s.'" % (tts_modify(stop).replace("'", "\\'"), direction)).encode('utf-8'))
				else:
					os.popen((u"espeak -v mb/mb-de5 -s 40 'Nähxter Halt: %s. Ausstieg in Fahrtrichtung %s.'" % (tts_modify(stop).replace("'", "\\'"), direction)).encode('utf-8'))
			
			if will_stop:
				first_sleep = random.uniform(0, cycle_interval)
				second_sleep = cycle_interval - first_sleep
				time.sleep(first_sleep)
				
				client.set_stop_indicator(args.display, True)
				
				if not args.quiet:
					os.popen("aplay -q %s" % args.stop_jingle)
				
				time.sleep(second_sleep)
			else:
				time.sleep(cycle_interval)
			
			has_stopped = will_stop
		
		print ""

if __name__ == "__main__":
	main()
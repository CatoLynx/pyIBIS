#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler

import argparse
from datetime import datetime
import gobject
import ibis
from mpris2.player import Player
from dbus.mainloop.glib import DBusGMainLoop

def main():
	def _on_properties_changed(self, *_args, **kw):
		if _args and 'PlaybackStatus' in _args[1] and _args[1]['PlaybackStatus'] != 'Playing':
			client.set_text(args.display, "Paused", priority = args.pause_priority, client = args.client)
			client.set_stop_indicator(args.display, False)
		else:
			data = player.Metadata
			title = unicode(data['xesam:title'])
			artist = unicode(", ".join(data['xesam:artist']))
			album = unicode(data['xesam:album'])
			timestamp = datetime.strptime(unicode(data['xesam:contentCreated']), "%Y-%m-%dT%H:%M:%S")
			year = timestamp.year
			
			sequence = []
			sequence.append(client.make_text(title))
			sequence.append(client.make_text(artist))
			sequence.append(client.make_text("%s (%i)" % (album, year)))
			client.set_sequence(args.display, sequence, args.sequence_interval, priority = args.music_priority, client = args.client)
			client.set_stop_indicator(args.display, True)
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-host', '--host', type = str, default = "localhost")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	parser.add_argument('-d', '--display', type = int, choices = (0, 1, 2, 3))
	parser.add_argument('-mpr', '--music_priority', type = int, default = 0)
	parser.add_argument('-ppr', '--pause_priority', type = int, default = 0)
	parser.add_argument('-cl', '--client', type = str, default = "music_info.py")
	parser.add_argument('-pl', '--player', type = str, default = "spotify")
	parser.add_argument('-si', '--sequence-interval', type = int, default = 3)
	args = parser.parse_args()
	
	client = ibis.Client(args.host, args.port)
	
	DBusGMainLoop(set_as_default = True)
	uri = "org.mpris.MediaPlayer2.%s" % args.player.lower()
	player = Player(dbus_interface_info = {'dbus_uri': uri})
	player.PropertiesChanged = _on_properties_changed
	_on_properties_changed(None)
	mloop = gobject.MainLoop()
	mloop.run()

if __name__ == "__main__":
	main()
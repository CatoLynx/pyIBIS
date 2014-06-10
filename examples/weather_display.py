#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to fetch and display weather data.
This script is a client to the IBIS server.
"""

import argparse
import datetime
import ibis
import requests

class WeatherException(Exception):
	def __init__(self, message, code):
		self.message = message
		self.code = code
	
	def __str__(self):
		return "%s (Code: %s)" % (self.message, self.code)

def _timestamp_to_datetime(timestamp):
	return datetime.datetime.fromtimestamp(timestamp)

def _kelvin_to_celsius(value):
	return float("%.1f" % (value - 273.15))

def _mps_to_kmh(value):
	return float("%.1f" % (value * 3.6))

def _deg_to_dir(deg):
	directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
	idx = int(((deg % 360) + 11.25) / 22.5) % 16
	return directions[idx]

def _process_weather_item(item):
	item['description'] = item['description'].title()
	return item

def _optimize_current_weather_data(data):
	data['dt'] = _timestamp_to_datetime(data['dt'])
	data['sys']['sunrise'] = _timestamp_to_datetime(data['sys']['sunrise'])
	data['sys']['sunset'] = _timestamp_to_datetime(data['sys']['sunset'])
	
	data['main']['temp'] = _kelvin_to_celsius(data['main']['temp'])
	data['main']['temp_min'] = _kelvin_to_celsius(data['main']['temp_min'])
	data['main']['temp_max'] = _kelvin_to_celsius(data['main']['temp_max'])
	
	data['wind']['speed'] = _mps_to_kmh(data['wind']['speed'])
	
	if 'deg' in data['wind']:
		data['wind']['deg'] = _deg_to_dir(data['wind']['deg'])
	else:
		data['wind']['deg'] = "?"
	
	for idx, item in enumerate(data['weather']):
		data['weather'][idx] = _process_weather_item(item)
	return data

def _optimize_daily_forecast_weather_data(data):
	for idx, item in enumerate(data['list']):
		data['list'][idx]['deg'] = _deg_to_dir(item['deg'])
		data['list'][idx]['dt'] = _timestamp_to_datetime(item['dt'])
		data['list'][idx]['speed'] = _mps_to_kmh(item['speed'])
		data['list'][idx]['rain'] = item['rain'] if 'rain' in item else 0
		data['list'][idx]['snow'] = item['snow'] if 'snow' in item else 0
		
		for key, value in item['temp'].iteritems():
			data['list'][idx]['temp'][key] = _kelvin_to_celsius(value)
		
		for idx2, item2 in enumerate(item['weather']):
			data['list'][idx]['weather'][idx2] = _process_weather_item(item2)
	return data

def _optimize_hourly_forecast_weather_data(data):
	for idx, item in enumerate(data['list']):
		data['list'][idx]['dt'] = _timestamp_to_datetime(item['dt'])
		data['list'][idx]['main']['temp'] = _kelvin_to_celsius(item['main']['temp'])
		data['list'][idx]['main']['temp_min'] = _kelvin_to_celsius(item['main']['temp_min'])
		data['list'][idx]['main']['temp_max'] = _kelvin_to_celsius(item['main']['temp_max'])
		if 'wind' in item:
			data['list'][idx]['wind']['speed'] = _mps_to_kmh(item['wind']['speed'])
			data['list'][idx]['wind']['deg'] = _deg_to_dir(item['wind']['deg'])
		else:
			data['list'][idx]['wind'] = {}
			data['list'][idx]['wind']['speed'] = 0
			data['list'][idx]['wind']['deg'] = "?"
		
		for idx2, item2 in enumerate(item['weather']):
			data['list'][idx]['weather'][idx2] = _process_weather_item(item2)
	return data

def _get_current_weather(city):
	resp = requests.get("http://api.openweathermap.org/data/2.5/weather?q=%s" % city)
	raw_weather = resp.json()
	
	if 'message' in raw_weather:
		# An error occurred
		raise WeatherException(message = raw_weather['message'], code = raw_weather['cod'])
	
	weather = _optimize_current_weather_data(raw_weather)
	return weather

def _get_daily_forecast_weather(city, days = 1):
	resp = requests.get("http://api.openweathermap.org/data/2.5/forecast/daily?q=%s&cnt=%i" % (city, days))
	raw_weather = resp.json()
	
	if raw_weather['cod'] != "200":
		# An error occurred
		raise WeatherException(message = raw_weather['message'], code = raw_weather['cod'])
	
	weather = _optimize_daily_forecast_weather_data(raw_weather)
	return weather

def _get_hourly_forecast_weather(city):
	resp = requests.get("http://api.openweathermap.org/data/2.5/forecast?q=%s" % city)
	raw_weather = resp.json()
	
	if raw_weather['cod'] != "200":
		# An error occurred
		raise WeatherException(message = raw_weather['message'], code = raw_weather['cod'])
	
	weather = _optimize_hourly_forecast_weather_data(raw_weather)
	return weather

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-host', '--host', type = str, default = "localhost")
	parser.add_argument('-p', '--port', type = int, default = 4242)
	parser.add_argument('-d', '--display', type = int, choices = (0, 1, 2, 3))
	parser.add_argument('-pr', '--priority', type = int, default = 0)
	parser.add_argument('-cl', '--client', type = str, default = "weather_display.py")
	parser.add_argument('-dn', '--duration', type = float, default = 5.0)
	parser.add_argument('-c', '--city', type = str, required = True, help = "The city to fetch weather data for")
	parser.add_argument('-m', '--mode', type = str, choices = ('current', 'forecast-daily', 'forecast-hourly'), default = 'current')
	parser.add_argument('-i', '--items', type = int, default = 1)
	parser.add_argument('-f', '--format', type = str, choices = ('detailed', 'brief', 'minimal'), default = 'detailed')
	args = parser.parse_args()
	
	client = ibis.Client(args.host, args.port)
	
	try:
		if args.mode == 'current':
			weather = _get_current_weather(args.city)
			if args.format == 'detailed':
				sequence = []
				sequence.append(client.make_text("%(description)s" % weather['weather'][0], args.duration))
				sequence.append(client.make_text("Temp: %(temp).1fC" % weather['main'], args.duration))
				sequence.append(client.make_text("Wind: %(speed).1f km/h from %(deg)s" % weather['wind'], args.duration))
				sequence.append(client.make_text("Hum: %(humidity)i%%, %(pressure).1f hPa" % weather['main'], args.duration))
				sequence.append(client.make_text("Cloudiness: %(all)i%%" % weather['clouds'], args.duration))
				sequence.append(client.make_text("Sun from %s to %s" % (
					weather['sys']['sunrise'].strftime("%H:%M"),
					weather['sys']['sunset'].strftime("%H:%M")
					), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'brief':
				sequence = []
				sequence.append(client.make_text("%(description)s" % weather['weather'][0], args.duration))
				sequence.append(client.make_text("%.1fC, %.1f km/h, %i%%" % (weather['main']['temp'], weather['wind']['speed'], weather['main']['humidity']), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'minimal':
				client.set_text(args.display, "%.1f / %.1f / %i / %.1f" % (
					weather['main']['temp'],
					weather['wind']['speed'],
					weather['main']['humidity'],
					weather['main']['pressure']
					), priority = args.priority, client = args.client)
		
		elif args.mode == 'forecast-daily':
			weather = _get_daily_forecast_weather(args.city, args.items)
			if args.format == 'detailed':
				sequence = []
				for day in weather['list']:
					sequence.append(client.make_text("(%s) %s, %i%% cloudy" % (
						day['dt'].strftime("%a"),
						day['weather'][0]['main'],
						day['clouds']
						), args.duration))
					sequence.append(client.make_text("(%s) %.1f %.1f %.1f %.1f" % (
						day['dt'].strftime("%a"),
						day['temp']['morn'],
						day['temp']['day'],
						day['temp']['eve'],
						day['temp']['night']
						), args.duration))
					sequence.append(client.make_text("(%s) %.1f km/h from %s" % (
						day['dt'].strftime("%a"),
						day['speed'],
						day['deg']
						), args.duration))
					sequence.append(client.make_text("(%s) %i%%, %.1f hPa" % (
						day['dt'].strftime("%a"),
						day['humidity'],
						day['pressure']
						), args.duration))
					sequence.append(client.make_text("(%s) Precip: %.1fmm" % (
						day['dt'].strftime("%a"),
						day['rain']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'brief':
				sequence = []
				for day in weather['list']:
					sequence.append(client.make_text("(%s) %s, %.1f-%.1fC" % (
						day['dt'].strftime("%a"),
						day['weather'][0]['main'],
						day['temp']['min'],
						day['temp']['max']
						), args.duration))
					sequence.append(client.make_text("(%s) %.1f km/h, %i%%" % (
						day['dt'].strftime("%a"),
						day['speed'],
						day['humidity']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'minimal':
				sequence = []
				for day in weather['list']:
					sequence.append(client.make_text("(%s) %.1f / %.1f / %i" % (
						day['dt'].strftime("%a"),
						day['temp']['day'],
						day['speed'],
						day['humidity']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
		
		elif args.mode == 'forecast-hourly':
			weather = _get_hourly_forecast_weather(args.city)
			if args.format == 'detailed':
				sequence = []
				for time in weather['list'][:args.items]:
					sequence.append(client.make_text("(%s) %s, %.1fC" % (
						time['dt'].strftime("%H:%M"),
						time['weather'][0]['main'],
						time['main']['temp']
						), args.duration))
					sequence.append(client.make_text("(%s) %i%%, %.1f hPa" % (
						time['dt'].strftime("%H:%M"),
						time['main']['humidity'],
						time['main']['pressure']
						), args.duration))
					sequence.append(client.make_text("(%s) %.1f km/h from %s" % (
						time['dt'].strftime("%H:%M"),
						time['wind']['speed'],
						time['wind']['deg']
						), args.duration))
					sequence.append(client.make_text("(%s) %i%% cloudy" % (
						time['dt'].strftime("%H:%M"),
						time['clouds']['all']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'brief':
				sequence = []
				for time in weather['list'][:args.items]:
					sequence.append(client.make_text("(%s) %s, %.1fC" % (
						time['dt'].strftime("%H:%M"),
						time['weather'][0]['main'],
						time['main']['temp']
						), args.duration))
					sequence.append(client.make_text("(%s) %.1f km/h, %i%%" % (
						time['dt'].strftime("%H:%M"),
						time['wind']['speed'],
						time['main']['humidity']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
			elif args.format == 'minimal':
				sequence = []
				for time in weather['list'][:args.items]:
					sequence.append(client.make_text("(%s) %.1f / %.1f / %i" % (
						time['dt'].strftime("%H:%M"),
						time['main']['temp'],
						time['wind']['speed'],
						time['main']['humidity']
						), args.duration))
				client.set_sequence(args.display, sequence, args.duration, priority = args.priority, client = args.client)
	except WeatherException:
		client.set_stop_indicator(args.display, True)
		client.set_text(args.display, "Couldn't fetch weather.", priority = args.priority, client = args.client)

if __name__ == "__main__":
	main()
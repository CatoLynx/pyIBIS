# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Tool to graphically simulate the text display
(For now, it's specific to the kind of display I have, feel free to modify the font files to suit your needs)
"""

import json
import os
from PIL import Image, ImageDraw

class DisplayFontScanner(object):
	"""
	Class to scan the PNG files that make up the font and create a representation
	of the font that can be programmatically used.
	
	There must be a <dotspacing / 2> pixel border on all sides of the image.
	Each dot must be <dotsize> pixels in diameter and the spacing between adjacent dots
	must be <dotspacing> pixels.
	Inactive dots must be gray, active dots must be any other color.
	"""
	
	def __init__(self, dotsize = 47, dotspacing = 8):
		self.dotsize = dotsize
		self.dotspacing = dotspacing
	
	def get_real_coordinates(self, x, y):
		"""
		Calculate the real x and y pixel coordinates from x and y dot coordinates
		"""
		
		real_x = (self.dotspacing / 2) + x * self.dotspacing + (x + 1) * self.dotsize - (self.dotsize / 2)
		real_y = (self.dotspacing / 2) + y * self.dotspacing + (y + 1) * self.dotsize - (self.dotsize / 2)
		
		return real_x, real_y
		
	def get_dot(self, image, x, y):
		"""
		Get the state of the dot at the given coordinates
		image must be a PIL Image instance
		"""
		
		real_x, real_y = self.get_real_coordinates(x, y)
		r, g, b = image.getpixel((real_x, real_y))[:3]
		state = not r == g == b # Check if dot is gray
		
		return state
	
	def build_char_data(self, image):
		"""
		Build the character data from the given PIL Image instance
		"""
		
		width = divmod(image.size[0], (self.dotsize + self.dotspacing))[0]
		height = divmod(image.size[1], (self.dotsize + self.dotspacing))[0]
		
		dots = []
		for y in range(height):
			row = []
			for x in range(width):
				row.append(self.get_dot(image, x, y))
			dots.append(row)
		
		char_data = {
			'width': width,
			'height': height,
			'dots': dots,
		}
		
		return char_data
		
	def scan_file(self, filename):
		"""
		Scan a single PNG file and build the character data for it
		"""
		
		image = Image.open(filename)
		char_data = self.build_char_data(image)
		
		return char_data
	
	def scan_font(self, fontdir, outfile):
		"""
		Scan the font folder and build the font map
		"""
		
		fontmap = {}
		files = [os.path.join(fontdir, filename) for filename in os.listdir(fontdir)]
		
		for filename in files:
			char_name = os.path.basename(filename)[:-4]
			try:
				char_data = self.scan_file(filename)
			except:
				continue
			if char_name == "slash":
				char_name = "/"
			fontmap[char_name] = char_data
		
		with open(outfile, 'w') as f:
			json.dump(fontmap, f)
		
		return fontmap

class DisplayFontGenerator(object):
	"""
	Class to do the reverse of what the DisplayFontScanner is doing.
	Generates images from a fontmap.
	"""
	
	def __init__(self, dotsize = 47, dotspacing = 8):
		self.dotsize = dotsize
		self.dotspacing = dotspacing
	
	def get_real_coordinates(self, x, y):
		"""
		Calculate the real x and y pixel coordinates from x and y dot coordinates
		"""
		
		real_x = (self.dotspacing / 2) + x * self.dotspacing + (x + 1) * self.dotsize - (self.dotsize / 2)
		real_y = (self.dotspacing / 2) + y * self.dotspacing + (y + 1) * self.dotsize - (self.dotsize / 2)
		
		return real_x, real_y
	
	def get_bounding_box(self, x, y, size):
		"""
		Get the bounding box coordinates for drawing a circle with the diameter <size>
		"""
		
		x0 = x - (size / 2)
		y0 = y - (size / 2)
		x1 = x + (size / 2)
		y1 = y + (size / 2)
		
		return x0, y0, x1, y1
	
	def generate_image(self, char_data, outfile, inactive_color, active_color, bg_color):
		"""
		Generate a single image from a character map.
		"""
		
		width = char_data['width']
		height = char_data['height']
		dots = char_data['dots']
		
		im_width = width * (self.dotsize + self.dotspacing)
		im_height = height * (self.dotsize + self.dotspacing)
		
		image = Image.new("RGB", (im_width, im_height), bg_color)
		draw = ImageDraw.Draw(image)
		
		for y, row in enumerate(dots):
			for x, state in enumerate(row):
				color = active_color if state else inactive_color
				
				# Workaround because with dotsize 1 ellipses become invisible
				if self.dotsize > 1:
					center_x, center_y = self.get_real_coordinates(x, y)
					box = self.get_bounding_box(center_x, center_y, self.dotsize)
					draw.ellipse(box, fill = color)
				else:
					draw.point((x, y), fill = color)
		
		if type(outfile) is str:
			with open(outfile.encode('utf-8'), 'wb') as f:
				image.save(f, "PNG")
		else:
			image.save(outfile, "PNG")
	
	def generate_font(self, fontmap_file, outdir, inactive_color = (64, 64, 64), active_color = (192, 255, 0), bg_color = (0, 0, 0)):
		"""
		Generate all images for a given fontmap
		"""
		
		with open(fontmap_file, 'r') as f:
			fontmap = json.load(f)
		
		for char, char_data in fontmap.iteritems():
			name = ("slash" if char == "/" else char) + ".png"
			filename = os.path.join(outdir, name)
			self.generate_image(char_data, filename, inactive_color, active_color, bg_color)

class DisplayFont(object):
	"""
	This class represents a display font used to display text.
	"""
	
	def __init__(self, fontmap_file, spacing):
		self.fontmap_file = fontmap_file
		self.spacing = spacing
		with open(self.fontmap_file, 'r') as f:
			self.fontmap = json.load(f)
	
	def get_width(self, text):
		length = len(text)
		width = 0
		for index, char in enumerate(text):
			if char in self.fontmap.keys():
				char_data = self.fontmap[char]
				width += char_data['width']
				if index < length - 1:
					width += self.spacing
		
		return width
	
	def get_nominal_width(self, text = "ABCDEabcde12345"):
		"""
		Calculate the average character width, used for sorting fonts based on the
		space the characters take
		"""
		
		avg_width = self.get_width(text) / len(text)
		
		return avg_width
	
	def generate_text_data(self, text):
		"""
		Generate dot data for an image representing the given text
		"""
		
		text_dots = []
		
		for index, char in enumerate(text):
			if char not in self.fontmap.keys():
				continue
			
			char_data = self.fontmap[char]
			dots = char_data['dots']
			
			for y, row in enumerate(dots):
				try:
					text_dots[y] += row
				except IndexError:
					text_dots.append(row[:]) # WITHOUT THE [:] SHIT GOES TO HELL
				
				if index < len(text) - 1:
					text_dots[y] += [False] * self.spacing
		
		width = len(text_dots[0])
		height = len(text_dots)
		
		text_data = {
			'width': width,
			'height': height,
			'dots': text_dots,
		}
		
		return text_data

class DisplaySimulator(object):
	"""
	Class that manages DisplayFonts and simulates the graphical display of the real displays
	
	The 'fonts' parameter must list the fonts from widest to narrowest font
	"""
	
	def __init__(self, fonts, width = 120, height = 8):
		self.fonts = fonts
		self.width = width
		self.height = height
	
	def choose_font(self, text):
		"""
		Choose the font that best fills the available space for the given text
		"""
		
		for font in self.fonts:
			if font.get_width(text) <= self.width:
				return font
		
		return self.fonts[-1] # Return the narrowest font in case no font is small enough
	
	def generate_image(self, text, outfile, dotsize = 47, dotspacing = 8, inactive_color = (64, 64, 64), active_color = (192, 255, 0), bg_color = (0, 0, 0)):
		"""
		Generate an image representing the given text
		Returns an overflow flag and the dot data for analytical purposes
		"""
		
		font = self.choose_font(text)
		overflow = False
		
		while font.get_width(text) > self.width:
			overflow = True
			text = text[:-1]
		
		text_data = font.generate_text_data(text)
		
		for y, row in enumerate(text_data['dots']):
			if len(row) > self.width:
				row = row[:self.width]
			elif len(row) == self.width:
				pass
			else:
				diff = self.width - len(row)
				left = diff / 2
				right = diff - left
				text_data['dots'][y] = [False] * left + row + [False] * right
		
		text_data['width'] = self.width
		
		gen = DisplayFontGenerator(dotsize, dotspacing)
		gen.generate_image(text_data, outfile, inactive_color, active_color, bg_color)
		return overflow, text_data['dots']

def main():
	pass

if __name__ == "__main__":
	main()
#pyIBIS – A Python library for controlling IBIS displays

##License
This program is licensed under the AGPLv3. See the `LICENSE` file for more information.

##Installation
You can easily install pyIBIS using the Python Package Index. Just type:

	sudo pip install pyibis

To use it in your code, just `import ibis`.

##Client-Server System
I built a client-server system which is useful if you have some IBIS displays in your room and you want to control them over your local network.
The library contains `Client` and `Server` classes, to see how to use them, check out the `cmdline_client.py` and `cmdline_server.py` scripts in the `examples` folder.

##Graphical Display Simulation
**Note:** For the simulator to work, you need to have the `PIL` module installed.

The font simulation script (`ibis.simulation`) is useful if you want to see what a given text would look like on your display. Only dot-matrix displays are supported. You have to create an image file for every character your display can show though. There's an example in the `simulation-font` directory which uses the font of my displays.
To use the simulator, enter an interactive Python shell (or write a script that does what you want). In the examples below, I'll assume that the simulator module is loaded as `ibis.simulation`.

###Terminology
* A **fontmap** is a JSON file that contains pixel data for all characters in a certain font. It is used to render images from text data.
* A **font directory**, **fontdir** for short, is a directory which contains image files for all characters in a font.

###Notes on filenames
The filenames in your fontdir should correspond to the character they're showing. The only exception to this is the file for the `/` character, which has to be named `slash.png` since `/` is not allowed in filenames even in the ext4 filesystem. I use only ext4 for my operating system, so that's the only file that will have to be renamed.
Should your filesystem impose further restrictions, you'll have to adapt the simulator script to suit your needs.

###Generating a fontmap from a fontdir
First, instantiate a `DisplayFontScanner`. The `dotsize` and `dotspacing` parameters tell it the size and the horizontal and vertical distance of the dots in your images, so it can parse them correctly. Let's use the default values:

	>>> my_scanner = ibis.simulation.DisplayFontScanner(dotsize = 47, dotspacing = 8)

Now, create the fontmap:

	>>> map = my_scanner.scan_font(fontdir = "~/myfont", outfile = "~/myfont.fontmap")

The `scan_font` method needs to know where to find the fontdir and where to save the fontmap. It also returns the fontmap as a `dict`.
That's it, now you have a fontmap!

###Generating an image using a fontmap
Begin by instantiating one or more `DisplayFont`s.
The `fontmap_file` parameter tells it which fontmap to use, the `spacing` parameter specifies the spacing (in dots) between any two characters using this font.

	>>> my_font = ibis.simulation.DisplayFont(fontmap_file = "~/myfont.fontmap", spacing = 2)

Now you can instantiate a `DisplaySimulator`.
The `fonts` parameter must be a sequence of `DisplayFont`s from widest to narrowest font (in case your display has multiple fonts, e.g. to fit more text on the screen)
The `width` and `height` parameters specify the width and height (in dots) of the simulated display.

	>>> my_simulator = ibis.simulation.DisplayFontSimulator(fonts = (my_font, ), width = 12, height = 8)

Now, render an image!

	>>> my_simulator.generate_image(text = "Hello world!", outfile = "~/hello_world.png")

That's it!
If you want to further customize the generated image, you can pass the following parameters to the `generate_image` method:

* `dotsize`: The size of the generated dots. Defaults to `47`.
* `dotspacing`: The horizontal and vertical spacing of the generated dots. Defaults to `8`.
* `inactive_color`: The color of inactive dots, in the form of a RGB tuple. Defaults to `(64, 64, 64)` (grey).
* `active_color`: The color of active dots, in the form of a RGB tuple. Defaults to `(192, 255, 0)` (green-yellow).
* `bg_color`: The color of the region between dots, in the form of a RGB tuple. Defaults to `(0, 0, 0)` (black).

###Generating a fontdir from a fontmap
First, instantiate a `DisplayFontGenerator`. The `dotsize` and `dotspacing` parameters act just like in a `DisplaySimulator`.

	>>> my_generator = ibis.simulation.DisplayFontGenerator(dotsize = 5, dotspacing = 2)

Now, generate your fontdir:

	>>> my_generator.generate_font(fontmap_file = "~/myfont.fontmap", outdir = "~/myfont_small")

This generates an image for every character in the fontmap. As with a `DisplaySimulator`, you can modify the `inactive_color`, `active_color` and `bg_color` parameters to suit your needs.
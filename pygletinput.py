import pyglet
from pyglet.gl import *
import pygletgui

if __name__ == "__main__":
    window = pygletgui.Window(resizable=True)
    window.set_location((window.screen.width / 2) - window.width/2,
                        (window.screen.height / 4) - window.height/2)
    pyglet.app.run()

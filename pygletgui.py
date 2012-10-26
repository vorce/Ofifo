# -*- coding: utf-8 -*-
import string
import subprocess
import pyglet
import Cocoa
import spotlightreader


class ResultHandler(Cocoa.NSObject):
    finished_func = None
    progress_func = None

    def awakeFromNib(self):
        pass

    def init(self):
        self = super(ResultHandler, self).init()
        return self

    def dealloc(self):
        Cocoa.NSNotificationCenter.defaultCenter().removeObserver_(self)

    def set_progress_func(self, func):
        self.progress_func = func

    def set_finished_func(self, func):
        self.finished_func = func

    def notificationHandler_(self, note):
        if note.name() == Cocoa.NSMetadataQueryDidStartGatheringNotification:
            pass
        elif note.name() == Cocoa.NSMetadataQueryDidFinishGatheringNotification:
            if self.finished_func:
                self.finished_func(note.object().results())
        elif note.name() == Cocoa.NSMetadataQueryGatheringProgressNotification:
            if self.progress_func:
                self.progress_func(note.object().results())
        elif note.name() == Cocoa.NSMetadataQueryDidUpdateNotification:
            pass


"""
Taken from http://www.pyglet.org/doc/programming_guide/text_input.py
"""


class Rectangle(object):
    '''Draws a rectangle into a batch.'''
    def __init__(self, x1, y1, x2, y2, batch):
        self.batch = batch
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
                                     ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
                                     ('c4B', [200, 200, 200, 255] * 4))

    def delete(self):
        self.vertex_list.delete()


class TextWidget(object):
    def __init__(self, text, x, y, width, batch):
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text),
            dict(color=(0, 0, 0, 255), font_size=28)
        )
        font = self.document.get_font()

        height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, height, multiline=False, batch=batch)
        self.layout.content_valign = "center"

        self.caret = pyglet.text.caret.Caret(self.layout)

        self.layout.x = x
        self.layout.y = y

        # Rectangular outline
        pad = 10
        self.rectangle = Rectangle(x - pad, y - pad,
                                   x + width + pad, y + height + pad, batch)

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def delete(self):
        self.layout.delete()
        self.rectangle.delete()


class TextButton(object):
    def __init__(self, text, path, x, y, width, batch):
        self.path_text = path
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text),
                                dict(color=(0, 0, 0, 255), font_size=20)
                               )
        font = self.document.get_font()
        self.height = font.ascent - font.descent

        self.path_doc = pyglet.text.document.UnformattedDocument(path)
        self.path_doc.set_style(0, len(self.path_doc.text),
                                dict(color=(100, 100, 100, 255), font_size=8))

        font = self.path_doc.get_font()
        path_height = font.ascent - font.descent

        self.batch = batch
        self.l2 = pyglet.text.layout.TextLayout(self.path_doc, width,
                                                path_height, batch=self.batch)
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, self.height, multiline=False, batch=self.batch)

        self.layout.x = x
        self.layout.y = y
        self.l2.x = x
        self.l2.y = y - path_height - 5
        #self.height -= path_height

        self.pad = 5
        self.width = width
        self.selected = False
        self.rectangle = Rectangle(x - self.pad, y - self.pad,
                                   x + self.width + self.pad,
                                   y + self.height + self.pad, self.batch)

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def delete(self):
        self.layout.delete()
        self.l2.delete()
        self.rectangle.delete()

    def select(self, selected):
        self.selected = selected

        if self.selected:
            self.document.set_style(0, len(self.document.text),
                                    dict(color=(250, 250, 250, 255)))
        else:
            self.document.set_style(0, len(self.document.text),
                                    dict(color=(0, 0, 0, 255)))


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(600, 80, caption='OfifO',
                                     style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        self.set_maximum_size(600, 450)

        self.batch = pyglet.graphics.Batch()
        self.search_matches = []
        self.predicate = "((kMDItemDisplayName LIKE[cd] '*{0}*') " + \
                         "OR (kMDItemFSName LIKE[cd] '*{0}*')) " + \
                         "AND (kMDItemContentType == 'com.apple.application-bundle')"
        self.search_paths = ["/Applications", "/Developers/Applications",
                             "/Library/PreferencePanes",
                             "/System/Library/PreferencePanes",
                             "/Users/joel"]

        self.widgets = [
            TextWidget('', 20, 20, self.width - 40, self.batch),
        ]
        self.text_cursor = self.get_system_mouse_cursor('text')

        self.focus = None
        self.focus_index = 0
        self.set_focus(self.widgets[0])
        self.reader = spotlightreader.SpotlightQuery.alloc().init()
        self.reader.query_handler = ResultHandler.alloc().init()
        #self.reader.query_handler.set_progress_func(self.search_progress)
        self.reader.query_handler.set_finished_func(self.search_finished)
        self.inited_search = False

    def on_resize(self, width, height):
        super(Window, self).on_resize(width, height)
        for widget in self.widgets:
            widget.layout.y = height - 60
            widget.rectangle.delete()
            widget.rectangle = Rectangle(10, height - 70, width - 10,
                                         (height - 70) + 60, self.batch)

    def on_draw(self):
        pyglet.gl.glClearColor(0.9, 0.9, 0.9, 1)
        self.clear()
        self.batch.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        for (path, name, widget) in self.search_matches:
            if widget.hit_test(x, y):
                print("Launch {0}: {1}".format(name, path))
                self.launch_app(path)

        if self.widgets[0].hit_test(x, y):
            self.widgets[0].caret.on_mouse_press(x, y, button, modifiers)

    def launch_app(self, path):
        subprocess.call(["open", path])
        pyglet.app.exit()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_text(self, text):
        self.widgets[0].caret.on_text(text)

        if text in string.whitespace:
            return

        val = self.widgets[0].document.text
        self.do_search(val)

    def do_search(self, word):
        if word in ["", string.whitespace]:
            return

        p = self.predicate.format(word.encode('utf-8'))

        if self.inited_search:
            self.reader.query.setPredicate_(
                Cocoa.NSPredicate.predicateWithFormat_(p))
        else:
            self.reader.new_search(Cocoa.NSPredicate.predicateWithFormat_(p),
                                   self.search_paths)
            self.inited_search = True

    def on_text_motion(self, motion):
        self.widgets[0].caret.on_text_motion(motion)

        if motion in [pyglet.window.key.MOTION_BACKSPACE,
                      pyglet.window.key.MOTION_DELETE]:
            self.do_search(self.widgets[0].document.text)

    def on_text_motion_select(self, motion):
        if self.focus:
            self.focus.caret.on_text_motion_select(motion)

    def search_finished(self, results):
        ypad = 60
        limited_results = results[:min(len(results), 10)]
        resize_height = 0

        for (path, name, widget) in self.search_matches:
            widget.delete()

        self.search_matches = []
        self.height = 80

        for i in limited_results:
            disp_name = i.valueForAttribute_("kMDItemDisplayName")

            path = i.valueForAttribute_("kMDItemPath")

            if path not in self.search_matches:
                resize_height += ypad
                self.search_matches.append((path, disp_name,
                                            TextButton(disp_name, path, 15,
                                                (self.height - 115) + resize_height,
                                                self.width - 30, self.batch)))

        if(len(limited_results) > 0):
            self.focus_index = len(self.search_matches) - 1
            self.set_focus(self.search_matches[self.focus_index][2])
        self.set_size(600, self.height + resize_height)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.DOWN and len(self.search_matches) > 0:
            self.focus_index -= 1
            self.set_focus(self.search_matches[self.focus_index %
                                               len(self.search_matches)][2])
        elif symbol == pyglet.window.key.UP and len(self.search_matches) > 0:
            self.focus_index += 1
            self.set_focus(self.search_matches[self.focus_index %
                                               len(self.search_matches)][2])
        elif symbol == pyglet.window.key.ENTER:
            if self.focus and len(self.search_matches) > 0:
                self.launch_app(self.search_matches[self.focus_index][0])

        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

    def set_focus(self, focus):
        if self.focus:
            try:
                self.focus.select(False)
            except AttributeError:
                pass

        self.focus = focus
        if self.focus:
            try:
                self.focus.caret.visible = True
                self.focus.caret.mark = 0
                self.focus.caret.position = len(self.focus.document.text)
            except AttributeError:
                try:
                    self.focus.select(True)
                except AttributeError:
                    pass

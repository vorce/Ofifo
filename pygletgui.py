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
            dict(color=(0, 0, 0, 255), font_size=30)
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
        self.batch = batch
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, self.height, multiline=False, batch=self.batch)

        self.layout.x = x
        self.layout.y = y

        self.pad = 5
        self.width = width
        self.rectangle = Rectangle(x - self.pad, y - self.pad,
                                   x + self.width + self.pad,
                                   y + self.height + self.pad, self.batch)

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def delete(self):
        self.layout.delete()
        self.rectangle.delete()

    def move_to(self, x, y):
        self.layout.x = x
        self.layout.y = y
        self.rectangle.delete()
        self.rectangle = Rectangle(x - self.pad, y - self.pad,
                                   x + self.width + self.pad,
                                   y + self.height + self.pad, self.batch)


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(600, 80, caption='OfifO',
                                     style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        self.need_reshuffle = False
        self.set_maximum_size(600, 450)
        self.button_list = []

        self.batch = pyglet.graphics.Batch()
        #self.labels = [
            #pyglet.text.Label('Name', x=10, y=100, anchor_y='bottom',
            #                  color=(0, 0, 0, 255), batch=self.batch),
            #pyglet.text.Label('Species', x=10, y=60, anchor_y='bottom',
            #                  color=(0, 0, 0, 255), batch=self.batch),
            #pyglet.text.Label('Special abilities', x=10, y=20,
            #                  anchor_y='bottom', color=(0, 0, 0, 255),
            #                  batch=self.batch)
        #]

        self.search_matches = {}
        self.predicate = "((kMDItemDisplayName LIKE[cd] '*{0}*') OR (kMDItemFSName LIKE[cd] '*{0}*')) AND (kMDItemContentType == 'com.apple.application-bundle')"
        self.search_paths = ["/Applications", "/Developers/Applications",
                             "/Library/PreferencePanes",
                             "/System/Library/PreferencePanes",
                             "/Users/joel"]

        self.widgets = [
            TextWidget('', 20, 20, self.width - 40, self.batch),
            #TextWidget('', 200, 60, self.width - 210, self.batch),
            #TextWidget('', 200, 20, self.width - 210, self.batch)
        ]
        self.text_cursor = self.get_system_mouse_cursor('text')

        self.focus = None
        self.set_focus(self.widgets[0])
        self.reader = spotlightreader.SpotlightQuery.alloc().init()
        self.reader.query_handler = ResultHandler.alloc().init()
        #self.reader.query_handler.set_progress_func(self.search_progress)
        self.reader.query_handler.set_finished_func(self.search_progress)
        #spotlightreader.SpotlightNotificationHandler.alloc().init()
        self.inited_search = False

    def on_resize(self, width, height):
        super(Window, self).on_resize(width, height)
        for widget in self.widgets:
            #widget.layout.y = widget.layout.y - 50
            #widget.width = width - 110
            widget.layout.y = height - 60
            widget.rectangle.delete()
            widget.rectangle = Rectangle(10, height - 70, width - 10,
                                         (height - 70) + 60, self.batch)

        #if self.need_reshuffle:
        #    y_pos = (self.height - 165)
        #    for key in self.search_matches:
        #        (n, widget) = self.search_matches[key]
        #        y_pos += 50
        #        widget.move_to(15, y_pos)
        #    need_reshuffle = False

    def on_draw(self):
        pyglet.gl.glClearColor(0.9, 0.9, 0.9, 1)
        self.clear()
        self.batch.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        for widget in self.widgets:
            if widget.hit_test(x, y):
                self.set_mouse_cursor(self.text_cursor)
                break
        else:
            self.set_mouse_cursor(None)

    def on_mouse_press(self, x, y, button, modifiers):
        for widget in self.widgets:
            if widget.hit_test(x, y):
                self.set_focus(widget)
                break
        else:
            self.set_focus(None)

        for key in self.search_matches:
            (name, widget) = self.search_matches[key]
            if widget.hit_test(x, y):
                print("Launch {0}: {1}".format(name, key))
                self.launch_app(key)

        if self.focus:
            self.focus.caret.on_mouse_press(x, y, button, modifiers)

    def launch_app(self, path):
        subprocess.call(["open", path])
        pyglet.app.exit()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.focus:
            self.focus.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        if self.focus:
            self.focus.caret.on_text(text)

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
        if self.focus:
            self.focus.caret.on_text_motion(motion)

        if motion in [pyglet.window.key.MOTION_BACKSPACE,
                      pyglet.window.key.MOTION_DELETE]:
            self.do_search(self.widgets[0].document.text)

    def on_text_motion_select(self, motion):
        if self.focus:
            self.focus.caret.on_text_motion_select(motion)

    def search_progress(self, results):
        to_remove = []
        limited_results = results[:min(len(results), 10)]
        result_keys = [i.valueForAttribute_("kMDItemPath") for i in
                       limited_results]
        resize_height = 0

        """
        print("-------- search progress ----------")
        print("result keys: {0}".format(result_keys))

        for key in self.search_matches:
            if key not in result_keys:
                (name, widget) = self.search_matches[key]
                to_remove.append(key)
                if widget:
                    widget.delete()
                    resize_height -= 50
                    self.need_reshuffle = True
                    print("removed {0}: {1}".format(key, resize_height))
                    #self.height -= 50
                    #self.set_size(600, self.height - 50)

        for key in to_remove:
            self.search_matches.pop(key)
        """
        self.search_matches.clear()
        if self.button_list:
            for i in self.button_list:
                i.delete()
        self.button_list = []
        self.height = 80

        for i in limited_results:
            disp_name = i.valueForAttribute_("kMDItemDisplayName")

            path = i.valueForAttribute_("kMDItemPath")

            if path not in self.search_matches:
                #self.set_size(600, self.height + 50)
                resize_height += 50
                print("added {0}: {1}".format(path, resize_height))
                #self.height += 50
                #btn = TextButton(disp_name, path, 15,
                #                 (self.height - 115) + resize_height, self.width - 30,
                #                 self.batch)
                self.search_matches[path] = (disp_name, "koko")
        print("rearch_matches: {0}".format(self.search_matches))

        resize_height = 0
        for key in self.search_matches:
            resize_height += 50
            (name, w) = self.search_matches[key]
            btn = TextButton(name, path, 15,
                             (self.height - 115) + resize_height, self.width - 30,
                             self.batch)
            self.button_list.append(btn)
        #if resize_height != 0:
        self.set_size(600, self.height + resize_height)

    def on_key_press(self, symbol, modifiers):
        """if symbol == pyglet.window.key.TAB:
            if modifiers & pyglet.window.key.MOD_SHIFT:
                dir = -1
            else:
                dir = 1

            if self.focus in self.widgets:
                i = self.widgets.index(self.focus)
            else:
                i = 0
                dir = 0

            self.set_focus(self.widgets[(i + dir) % len(self.widgets)])
        """

        if symbol == pyglet.window.key.ENTER:
            #self.set_size(600, self.height + 50)
            #TextButton('abc', 15, self.height - 110, self.width - 30,
            #            self.batch)
            #Rectangle(20, 100,
            #          500, 50, self.batch)
            pass

        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

    def set_focus(self, focus):
        if self.focus:
            self.focus.caret.visible = False
            self.focus.caret.mark = self.focus.caret.position = 0

        self.focus = focus
        if self.focus:
            self.focus.caret.visible = True
            self.focus.caret.mark = 0
            self.focus.caret.position = len(self.focus.document.text)

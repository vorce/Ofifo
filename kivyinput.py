import sys
import kivy
import kivy.app
import kivy.uix.textinput
import kivy.uix.boxlayout
import kivy.uix.button
import Cocoa
import spotlightreader

"""
class SpotlightNotificationHandler(Cocoa.NSObject):
    def awakeFromNib(self):
        pass

    def init(self):
        self = super(SpotlightNotificationHandler, self).init()
        return self

    def notificationHandler_(self, note):
        if note.name() == Cocoa.NSMetadataQueryDidFinishGatheringNotification:
            print("All done niggah")
            sys.exit(0)
            """

class OfifoKivy(kivy.app.App):
    inited_search = False
    predicate = "((kMDItemDisplayName LIKE[cd] '*{0}*') OR (kMDItemFSName LIKE[cd] '*{0}*')) AND (kMDItemContentType == 'com.apple.application-bundle')"
    search_paths = ["/Applications", "/Developers/Applications",
                    "/Library/PreferencePanes", "/System/Library/PreferencePanes",
                    "/Users/joel"]
    search_matches = {}

    def notificationHandler_(self, note):
        if note.name() == Cocoa.NSMetadataQueryDidStartGatheringNotification:
            print("Started gathering...")
        elif note.name() == Cocoa.NSMetadataQueryDidFinishGatheringNotification:
            result = note.object().results()

            print("Finished gathering. Found {0} matches".format(
                len(result)))
            for i in result:
                disp_name = i.valueForAttribute_("kMDItemDisplayName").encode('UTF-8')
                path = i.valueForAttribute_("kMDItemPath").encode('UTF-8')

                print("{0} ({1})".format(disp_name, path))
                #        i.valueForAttribute_("kMDItemContentType").decode('UTF-8')))
            
            print("-------------")
            #AppHelper.stopEventLoop()
            #sys.exit(0)
        elif note.name() == Cocoa.NSMetadataQueryGatheringProgressNotification:
            print("Progress event...")
            for key in self.search_matches:
                (name, widget) = self.search_matches[key]
                self.layout.remove_widget(widget)
            self.search_matches = {}

            for i in note.object().results():
                disp_name = i.valueForAttribute_("kMDItemDisplayName").encode('UTF-8')
                path = i.valueForAttribute_("kMDItemPath").encode('UTF-8')

                print("{0} ({1})".format(disp_name, path))

                if not self.search_matches.has_key(path):
                    btn = kivy.uix.button.Button(text=disp_name)
                    self.search_matches[path] = (disp_name, btn)
                    self.layout.add_widget(btn)

        elif note.name() == Cocoa.NSMetadataQueryDidUpdateNotification:
            print("Update")

    def on_enter(self, value):
        pass

    def on_text(self, instance, value):
        if value == "":
            return

        print("Creating new search for: {0}".format(value))
        #predicate = "(kMDItemFSName BEGINSWITH[cd] '{0}')".format(value)
        #  AND kMDItemContentType == 'com.apple.application-bundle'
        p = self.predicate.format(value)
        #predicate = "(kMDItemDisplayName BEGINSWITH[cd] '{0}') AND
        #(kMDItemContentType == 'com.apple.application-bundle')".format(value)

        if self.inited_search:
            self.reader.query.setPredicate_(Cocoa.NSPredicate.predicateWithFormat_(p))
        else:
            self.reader.new_search(Cocoa.NSPredicate.predicateWithFormat_(p), self.search_paths, self)
            self.inited_search = True

    def on_focus(self, instance, value):
        if not value:
            sys.exit(0)

    def build(self):
        self.text_input = kivy.uix.textinput.TextInput(focus=True, multiline=False)
        self.text_input.bind(on_text_validate=self.on_enter)
        self.text_input.bind(text=self.on_text)
        self.text_input.bind(focus=self.on_focus)

        self.layout = kivy.uix.boxlayout.BoxLayout(orientation='vertical')
        self.layout.add_widget(self.text_input)

        self.reader = spotlightreader.SpotlightQuery.alloc().init()

        return self.layout

if __name__ == '__main__':
    OfifoKivy().run()


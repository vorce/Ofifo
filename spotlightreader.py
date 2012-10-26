# -*- coding: utf-8 -*-
"""
"""
import sys
from Cocoa import *
from PyObjCTools import AppHelper


class SpotlightNotificationHandler(NSObject):
    def awakeFromNib(self):
        pass

    def init(self):
        self = super(SpotlightNotificationHandler, self).init()
        return self

    def notificationHandler_(self, note):
        if note.name() == NSMetadataQueryDidFinishGatheringNotification:
            print("All done niggah")
        elif note.name() == NSMetadataQueryGatheringProgressNotification:
            print("Da Progress event...")

    def dealloc(self):
        NSNotificationCenter.defaultCenter().removeObserver_(self)


class SpotlightQuery(NSObject):
    query = objc.ivar()
    query_handler = None

    def awakeFromNib(self):
        pass

    def init(self):
        self = super(SpotlightQuery, self).init()
        return self

    def new_search(self, pred, search_scopes=None):
        self.query = NSMetadataQuery.alloc().init()

        nf = NSNotificationCenter.defaultCenter()

        if self.query_handler is None:
            nf.addObserver_selector_name_object_(self, 'queryNotification:',
                                                 None, self.query)
        else:
            nf.addObserver_selector_name_object_(self.query_handler,
                                                 'notificationHandler:',
                                                 None, self.query)

        if search_scopes is not None:
            #print("Setting search paths to: {0}".format(search_scopes))
            self.query.setSearchScopes_(search_scopes)

        if self.query.isStarted or self.query.isGathering:
            self.query.stopQuery()
            #print("Stopping already running query")

        self.query.setPredicate_(pred)

        if (not self.query.isStarted) or self.query.isStopped:
            #print("Starting new query with pred: {0}".format(pred))
            self.query.startQuery()

    def queryNotification_(self, note):
        if note.name() == NSMetadataQueryDidStartGatheringNotification:
            print("Search: Started gathering...")
        elif note.name() == NSMetadataQueryDidFinishGatheringNotification:
            result = note.object().results()

            print("Search: Finished gathering. Found {0} matches".format(
                len(result)))
            for i in result:
                print("{0} ({1})".format(
                          i.valueForAttribute_("kMDItemDisplayName").encode('utf-8'),
                          i.valueForAttribute_("kMDItemPath").encode('utf-8')))
            print("-------------")
            #AppHelper.stopEventLoop()
            #sys.exit(0)
        elif note.name() == NSMetadataQueryGatheringProgressNotification:
            print("Search: Progress event...")
        elif note.name() == NSMetadataQueryDidUpdateNotification:
            print("Search: Update")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Pass a search word as argument")
        sys.exit(0)

    predicate = "(kMDItemFSName BEGINSWITH[cd] '{0}')".format(sys.argv[1])
    # https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/Predicates/Articles/pSyntax.html#//apple_ref/doc/uid/TP40001795

    handler = SpotlightNotificationHandler.alloc().init()

    qt = SpotlightQuery.alloc().init()
    qt.new_search(NSPredicate.predicateWithFormat_(predicate), handler)
    AppHelper.runConsoleEventLoop(installInterrupt=True)


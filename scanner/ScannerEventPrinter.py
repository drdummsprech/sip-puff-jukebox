from scanner.ScannerEvents import ScannerEventHandler, ScannerEvent, RootPathRemoved, AudioFileFound, RootPathAppeared


class ScannerEventPrinter(ScannerEventHandler):

    def handle_scanner_event(self, event: ScannerEvent):
        if isinstance(event, RootPathRemoved):
            print("Root path was removed: " + event.rootPath.__str__())
        if isinstance(event, RootPathAppeared):
            print("Root path was connected: " + event.rootPath.__str__())
        if isinstance(event, AudioFileFound):
            print("Found audio file: " + event.path.__str__() + " with gain: " + event.gain_level.__str__())
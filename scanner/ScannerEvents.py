""" Contains the events the Scanner produces """
from abc import ABC, abstractmethod
from pathlib import Path


class ScannerEvent:
    """ Base class for scanner events """


class ScannerEventHandler(ABC):
    """ Interface for anything that wants to process ScannerEvents"""

    @abstractmethod
    def handle_scanner_event(self, event: ScannerEvent):
        pass


class RootPathRemoved(ScannerEvent):
    """
    This event gets fired when a root path is not accessible anymore, e.g. after removing a thumbdrive.
    Any audio files that happen to be on this root path should be considered inaccesible after receiving this event.
    """
    rootPath: Path

    def __init__(self, root_path: Path):
        self.rootPath = root_path


class RootPathAppeared(ScannerEvent):
    """
    This event gets fired when a new root path becomes available, e.g. after plugging in a thumbdrive.
    """
    rootPath: Path

    def __init__(self, path: Path):
        self.rootPath = path


class AudioFileFound(ScannerEvent):
    """
    This event gets fired after an audio file has been processed and all necessary information for playback have been
    collected. This is currently only the gain level for correcting the perceived volume.
    """
    path: Path
    gain_level: float

    def __init__(self, path: Path, gain_level: float):
        self.path = path
        self.gain_level = gain_level

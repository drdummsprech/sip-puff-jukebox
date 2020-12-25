import json
import os
import sys
from enum import Enum
from pathlib import Path
from time import sleep

from scanner.Scan import get_gain_level, get_sha1_hash
from scanner.ScannerEvents import ScannerEventHandler, RootPathRemoved, AudioFileFound, RootPathAppeared


class AvailabilityChange(Enum):
    """Helper enum to describe the state transition of a root path's availability"""
    APPEARED = 1
    DISAPPEARED = 2
    NO_CHANGE = 3


class RootPath:
    """
    Describes a path that's the root of some file collection.
    In practice this is the mount directory for some thumbdrive.
    """
    path: Path
    __lastAvailableState = False

    def __init__(self, path: Path):
        self.path = path

    def check_availability(self) -> AvailabilityChange:
        """
        Checks whether this root path is currently accessible.
        :return: An enum describing the availability change
        """
        last_available = self.__lastAvailableState
        try:
            content = os.listdir(self.path)
            if content:
                self.__lastAvailableState = True
                if last_available:
                    return AvailabilityChange.NO_CHANGE
                else:
                    return AvailabilityChange.APPEARED
            else:
                self.__lastAvailableState = False
                if last_available:
                    return AvailabilityChange.DISAPPEARED
                else:
                    return AvailabilityChange.NO_CHANGE
        except:
            sys.stderr.write("Error checking availability for " + self.path.__str__() + "\n")
            self.__lastAvailableState = False
            if last_available:
                return AvailabilityChange.DISAPPEARED
            else:
                return AvailabilityChange.NO_CHANGE


class Scanner:
    """
    Scans root paths and emits events that describe the result of the audio file scanning.

    Attributes:
        root_paths          The root paths to scan. These are the mount points of the thumbdrives.
                            Default values are the mountpoints the package "usbmount" uses.
        audio_extensions    The file extensions we check for audio file content
        event_handler       The event handler that receives the events this scanner emits

    """

    root_paths: [RootPath] = [
        RootPath(Path("/media/usb0")),
        RootPath(Path("/media/usb1")),
        RootPath(Path("/media/usb2")),
        RootPath(Path("/media/usb3")),
        RootPath(Path("/media/usb4")),
        RootPath(Path("/media/usb5")),
        RootPath(Path("/media/usb6")),
        RootPath(Path("/media/usb7")),
    ]

    audio_extensions: [str] = [
        ".mp3",
        ".ogg",
        ".flac",
        ".wma",
    ]

    event_handler: ScannerEventHandler

    def __init__(self, event_handler: ScannerEventHandler):
        self.event_handler = event_handler

    def work_loop(self):
        """
        Scans all root paths for availability every 5 seconds.
        If a new root path becomes available, it's scanned recursively. In this case the time between successive
        checks of a given root path is prolongued by the time to scan the new root path.
        :return: None
        """
        while True:
            for rp in self.root_paths:
                change = rp.check_availability()
                if change == AvailabilityChange.NO_CHANGE:
                    continue
                elif change == AvailabilityChange.DISAPPEARED:
                    self.event_handler.handle_scanner_event(RootPathRemoved(rp.path))
                elif change.APPEARED:
                    self.event_handler.handle_scanner_event(RootPathAppeared(rp.path))
                    self.scan_path(rp)
            sleep(5)

    def scan_path(self, root_path: RootPath):
        """
        Recusrively scans all files on a root path for audio content.
        If a file is likely an audio file, its gain level is determined and an event is fired to broadcast its
        availability.
        :param root_path: The root path to scan
        :return: None. As a side effect AudioFileFound might be emitted
        """

        # check to see if there is a gain database on the root path
        gain_db: {str: float} = {}
        try:
            gain_db_path = os.path.join(root_path.path, "gain_database.json")
            with open(gain_db_path, 'r') as file_handle:
                gain_db = json.load(file_handle)
        except:
            pass

        for (dir_path, dirs, files) in os.walk(topdown=True, followlinks=False, top=root_path.path):
            for file in files:
                absolute_path = os.path.join(dir_path, file)

                try:
                    # Get the extension
                    ext = os.path.splitext(file)[-1].lower()
                    if ext in self.audio_extensions:
                        # Get the hash and see if we have a gain value in the db already
                        hash = get_sha1_hash(absolute_path)
                        if hash in gain_db:
                            self.event_handler.handle_scanner_event(AudioFileFound(Path(absolute_path), gain_db[hash]))
                            continue

                        # If we don't have a gain value, we just calculate it
                        gain = get_gain_level(absolute_path)
                        if gain is None:
                            sys.stderr.write("Could not get gain info for " + absolute_path.__str__() + "\n")
                        else:
                            self.event_handler.handle_scanner_event(AudioFileFound(Path(absolute_path), gain))
                except:
                    sys.stderr.write("Error scanning root path: " + root_path.path.__str__())

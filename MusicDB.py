import sys
from pathlib import Path
import random
from typing import Optional


class DbEntry:
    path: Path
    gain_level: float

    def __init__(self, path: Path, gain_level: float):
        self.path = path
        self.gain_level = gain_level


class MusicDB:
    """
    Class for storing information about the available music.
    """
    __data: {str: [DbEntry]} = {}

    def add_root_path(self, path: Path):
        self.__data[path.absolute().__str__()] = []

    def remove_root_path(self, path: Path):
        del self.__data[path.absolute().__str__()]

    def add_entry(self, path: Path, gain_level: float):
        for key in self.__data:
            if path.absolute().__str__().startswith(key):
                self.__data[key].append(DbEntry(path, gain_level))
                return
        sys.stderr.write("Root path for file not yet added: " + path.__str__() + "\n")

    def get_random_entry(self) -> Optional[DbEntry]:
        allKeys = list(self.__data.keys())
        keysWithContent = [k for k in allKeys if len(self.__data[k]) > 0]
        if not keysWithContent:
            return None
        key = random.choice(keysWithContent)
        entry = random.choice(self.__data[key])
        return entry

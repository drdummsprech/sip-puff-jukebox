import os
import sys
import json
from pathlib import Path

from scanner.Scan import get_gain_level, get_sha1_hash


class Prescanner:
    """Scanner for prescanning thumbdrives and retrieving a map of file hashes and gain levels"""

    audio_extensions: [str] = [
        ".mp3",
        ".ogg",
        ".flac",
        ".wma",
    ]

    def scan_root_path(self, scan_path: Path, output_path: Path):
        data: {str: float} = {}
        for (dir_path, dirs, files) in os.walk(topdown=True, followlinks=False, top=scan_path):
            for file in files:
                absolute_path = os.path.join(dir_path, file)

                # Get the extension
                ext = os.path.splitext(file)[-1].lower()
                if ext in self.audio_extensions:
                    gain = get_gain_level(absolute_path)
                    hash = get_sha1_hash(absolute_path)
                    if gain is not None and hash is not None:
                        data[hash] = gain
                        print("Added " + absolute_path.__str__() + " with gain " + gain.__str__())
                    else:
                        sys.stderr.write("Error scanning " + absolute_path.__str__() + "\n")

        # Write hash table as a JSON file
        json_dict = json.dumps(data)
        with open(output_path, 'x') as file_handle:
            file_handle.write(json_dict)

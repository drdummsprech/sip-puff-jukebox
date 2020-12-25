import hashlib
from typing import Optional

import r128gain


def get_gain_level(filepath) -> Optional[float]:
    """
    Takes a path to a file and calculates the gain level for the file using some external library.
    :param filepath: The file to get the gain level for
    :return: Either the gain level for the file or None, if it couldn't be determined
    """
    try:
        gain_info = r128gain.get_r128_loudness([filepath])
        if isinstance(gain_info[0], float):
            return gain_info[0]
        else:
            return None
    except:
        return None


def get_sha1_hash(filepath) -> Optional[str]:
    """
    Reads a file and returns its SHA1 hash as a hex string
    :param filepath: The file to hash
    :return: The hash as a hex string or None if some error occured
    """
    block_size = 2 ** 18  # 256kB
    sha1 = hashlib.sha1()

    try:
        with open(filepath, 'rb') as file_handle:
            while True:
                data = file_handle.read(block_size)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()
    except:
        return None

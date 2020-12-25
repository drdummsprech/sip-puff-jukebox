from pathlib import Path

from scanner.PreScanner import Prescanner

if __name__ == '__main__':
    prescanner = Prescanner()
    prescanner.scan_root_path(Path("/mnt/e"), Path("/mnt/e/gain_database.json"))

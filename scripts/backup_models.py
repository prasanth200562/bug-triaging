import shutil
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / 'saved_models'
# Place backups outside the `saved_models` directory to avoid recursive copying
BACKUP_ROOT = BASE / 'backups' / 'saved_models'

def backup_models():
    if not SRC.exists():
        print(f"No saved_models directory at {SRC}")
        return
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = BACKUP_ROOT / ts
    # copytree with ignore to skip any existing backup folders under SRC
    def _ignore(path, names):
        # ignore the target backup folder if it exists inside SRC
        return { 'backups', }
    shutil.copytree(SRC, dest, dirs_exist_ok=False, ignore=shutil.ignore_patterns('backups'))
    print(f"Backed up {SRC} -> {dest}")

if __name__ == '__main__':
    backup_models()

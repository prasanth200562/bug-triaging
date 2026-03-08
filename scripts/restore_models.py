from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[1]
BACKUP_ROOT = BASE / 'backups' / 'saved_models'
DEST = BASE / 'saved_models'

def latest_backup():
    if not BACKUP_ROOT.exists():
        return None
    subs = [p for p in BACKUP_ROOT.iterdir() if p.is_dir()]
    if not subs:
        return None
    return sorted(subs, key=lambda p: p.name)[-1]

def restore(backup_dir=None):
    if backup_dir is None:
        backup_dir = latest_backup()
    else:
        backup_dir = Path(backup_dir)

    if not backup_dir or not backup_dir.exists():
        print('No backup found to restore')
        return

    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(backup_dir, DEST)
    print(f'Restored {DEST} from {backup_dir}')

if __name__ == '__main__':
    # default: restore latest backup
    restore()

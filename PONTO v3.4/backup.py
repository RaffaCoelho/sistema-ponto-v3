import shutil, os, datetime
from typing import Optional

def export_sqlite(db_path: str, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.basename(db_path)
    out = os.path.join(dest_dir, f"{os.path.splitext(base)[0]}-backup-{ts}.sqlite")
    shutil.copy2(db_path, out)
    return out

def import_sqlite(src_file: str, db_path: str) -> str:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    shutil.copy2(src_file, db_path)
    return db_path

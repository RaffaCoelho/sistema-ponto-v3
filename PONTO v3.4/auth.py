import sqlite3
import hashlib
from typing import Optional, Tuple

# Simple auth for v3.2
# users table (if not exists): id, username, password_hash, role ('admin' or 'user'), person_id (to bind to own point)

def ensure_schema(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','user')),
        person_id INTEGER
    )
    """)
    con.commit()
    con.close()

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def create_user(db_path: str, username: str, password: str, role: str = 'user', person_id: Optional[int] = None):
    ensure_schema(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO users(username, password_hash, role, person_id) VALUES(?,?,?,?)",
                (username, hash_password(password), role, person_id))
    con.commit()
    con.close()

def login(db_path: str, username: str, password: str) -> Optional[Tuple[int, str, str, Optional[int]]]:
    ensure_schema(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id, username, role, person_id, password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    uid, uname, role, person_id, pwh = row
    if pwh == hash_password(password):
        return (uid, uname, role, person_id)
    return None

def is_admin(session) -> bool:
    return bool(session and len(session) >= 3 and session[2] == 'admin')

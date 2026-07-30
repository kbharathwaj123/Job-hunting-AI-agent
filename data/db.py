import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "applications.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            job_title TEXT,
            company TEXT,
            job_url TEXT UNIQUE,
            ats_score REAL,
            status TEXT,          -- found | tailored | staged | submitted | skipped | already_applied
            resume_path TEXT,
            applied_at TEXT,
            screenshot TEXT       -- Filepath to proof screenshot
        )
    """)
    # Add screenshot column if upgrading existing database
    try:
        conn.execute("ALTER TABLE applications ADD COLUMN screenshot TEXT")
    except Exception:
        pass
        
    conn.commit()
    conn.close()


def already_seen(job_url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT 1 FROM applications WHERE job_url = ? AND status != 'error'",
        (job_url,)
    ).fetchone()
    conn.close()
    return row is not None


def record(source, job_title, company, job_url, ats_score, status, resume_path="", screenshot=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO applications
           (source, job_title, company, job_url, ats_score, status, resume_path, applied_at, screenshot)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (source, job_title, company, job_url, ats_score, status, resume_path,
         datetime.now().isoformat(), screenshot),
    )
    conn.commit()
    conn.close()


def today_count() -> int:
    conn = sqlite3.connect(DB_PATH)
    today_str = datetime.now().date().isoformat()
    count = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE applied_at LIKE ? AND status IN ('submitted', 'staged', 'applied')",
        (f"{today_str}%",)
    ).fetchone()[0]
    conn.close()
    return count

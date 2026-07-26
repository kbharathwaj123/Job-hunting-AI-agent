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
            status TEXT,          -- found | tailored | staged | submitted | skipped
            resume_path TEXT,
            applied_at TEXT
        )
    """)
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


def record(source, job_title, company, job_url, ats_score, status, resume_path=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO applications
           (source, job_title, company, job_url, ats_score, status, resume_path, applied_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (source, job_title, company, job_url, ats_score, status, resume_path,
         datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def today_count() -> int:
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().date().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status='submitted' AND applied_at LIKE ?",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return row[0]

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "assessments.db"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS school_profile (
            id INTEGER PRIMARY KEY,
            school_name TEXT NOT NULL,
            school_website TEXT NOT NULL,
            created_on TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assessment_session (
            session_id TEXT PRIMARY KEY,
            module_id TEXT NOT NULL,
            school_name TEXT NOT NULL,
            created_on TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'in_progress',
            sections_complete TEXT NOT NULL DEFAULT '[]',
            sections_skipped TEXT NOT NULL DEFAULT '[]',
            overall_completion_percentage REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS answer_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            raw_answer TEXT,
            notes TEXT,
            answer_status TEXT NOT NULL DEFAULT 'unanswered',
            answered_on TEXT,
            last_modified TEXT,
            FOREIGN KEY (session_id) REFERENCES assessment_session(session_id),
            UNIQUE(session_id, question_id)
        );
    """)
    db.commit()
    db.close()


def save_answer(session_id, question_id, raw_answer, notes=None, status="answered"):
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute("""
        INSERT INTO answer_record
            (session_id, question_id, raw_answer, notes, answer_status, answered_on, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id, question_id) DO UPDATE SET
            raw_answer=excluded.raw_answer,
            notes=excluded.notes,
            answer_status=excluded.answer_status,
            last_modified=excluded.last_modified
    """, (session_id, question_id, json.dumps(raw_answer), notes, status, now, now))
    db.execute("""
        UPDATE assessment_session SET last_modified=? WHERE session_id=?
    """, (now, session_id))
    db.commit()
    db.close()


def get_answers(session_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM answer_record WHERE session_id=?", (session_id,)
    ).fetchall()
    db.close()
    result = {}
    for row in rows:
        result[row["question_id"]] = {
            "raw_answer": json.loads(row["raw_answer"]) if row["raw_answer"] else None,
            "notes": row["notes"],
            "answer_status": row["answer_status"],
            "answered_on": row["answered_on"],
        }
    return result


def get_answer(session_id, question_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM answer_record WHERE session_id=? AND question_id=?",
        (session_id, question_id)
    ).fetchone()
    db.close()
    if row:
        return {
            "raw_answer": json.loads(row["raw_answer"]) if row["raw_answer"] else None,
            "notes": row["notes"],
            "answer_status": row["answer_status"],
        }
    return None


def create_session(session_id, module_id, school_name):
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute("""
        INSERT OR IGNORE INTO assessment_session
            (session_id, module_id, school_name, created_on, last_modified, status)
        VALUES (?, ?, ?, ?, ?, 'in_progress')
    """, (session_id, module_id, school_name, now, now))
    db.commit()
    db.close()


def get_session(session_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM assessment_session WHERE session_id=?", (session_id,)
    ).fetchone()
    db.close()
    if row:
        return dict(row)
    return None


def mark_section_complete(session_id, section_id):
    db = get_db()
    row = db.execute(
        "SELECT sections_complete FROM assessment_session WHERE session_id=?",
        (session_id,)
    ).fetchone()
    if row:
        complete = json.loads(row["sections_complete"])
        if section_id not in complete:
            complete.append(section_id)
        now = datetime.utcnow().isoformat()
        db.execute("""
            UPDATE assessment_session
            SET sections_complete=?, last_modified=?
            WHERE session_id=?
        """, (json.dumps(complete), now, session_id))
        db.commit()
    db.close()


def get_all_sessions():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM assessment_session ORDER BY last_modified DESC"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def save_school_profile(school_name, school_website):
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute("DELETE FROM school_profile")
    db.execute(
        "INSERT INTO school_profile (school_name, school_website, created_on) VALUES (?,?,?)",
        (school_name, school_website, now)
    )
    db.commit()
    db.close()


def get_school_profile():
    db = get_db()
    row = db.execute("SELECT * FROM school_profile LIMIT 1").fetchone()
    db.close()
    return dict(row) if row else None

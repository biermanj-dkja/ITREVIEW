import sqlite3
import json
import os as _os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# When running as a PyInstaller bundle, the launcher sets SCHOOL_IT_DATA_DIR
# to a folder next to the executable so the database persists across restarts.
# In normal development use, fall back to the project-local data/ folder.
_data_dir = _os.environ.get('SCHOOL_IT_DATA_DIR')
if _data_dir:
    DB_PATH = Path(_data_dir) / "assessments.db"
else:
    DB_PATH = BASE_DIR / "data" / "assessments.db"


def get_db():
    db = sqlite3.connect(str(DB_PATH))
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
            sections_flagged TEXT NOT NULL DEFAULT '[]',
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

        CREATE TABLE IF NOT EXISTS answer_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            old_raw_answer TEXT,
            old_answer_status TEXT,
            new_raw_answer TEXT,
            new_answer_status TEXT,
            changed_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES assessment_session(session_id)
        );

        CREATE TABLE IF NOT EXISTS finding_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            finding_id TEXT NOT NULL,
            note TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(session_id, finding_id)
        );

        CREATE TABLE IF NOT EXISTS session_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            meta_key TEXT NOT NULL,
            meta_value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(session_id, meta_key)
        );
    """)
    # Migrate: add sections_flagged column if it doesn't exist yet
    try:
        db.execute("ALTER TABLE assessment_session ADD COLUMN sections_flagged TEXT NOT NULL DEFAULT '[]'")
        db.commit()
    except Exception:
        pass  # Column already exists
    # Migrate: add last_exported column if it doesn't exist yet
    try:
        db.execute("ALTER TABLE assessment_session ADD COLUMN last_exported TEXT")
        db.commit()
    except Exception:
        pass  # Column already exists
    # Migrate: add answer_history table if it doesn't exist yet
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS answer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                old_raw_answer TEXT,
                old_answer_status TEXT,
                new_raw_answer TEXT,
                new_answer_status TEXT,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES assessment_session(session_id)
            )
        """)
        db.commit()
    except Exception:
        pass
    # Migrate: add finding_context table if it doesn't exist yet
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS finding_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                note TEXT NOT NULL,
                added_at TEXT NOT NULL,
                UNIQUE(session_id, finding_id)
            )
        """)
        db.commit()
    except Exception:
        pass
    # Migrate: add session_meta table if it doesn't exist yet
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS session_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                meta_key TEXT NOT NULL,
                meta_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(session_id, meta_key)
            )
        """)
        db.commit()
    except Exception:
        pass
    db.commit()
    db.close()


def save_answer(session_id, question_id, raw_answer, notes=None, status="answered",
                record_history=False, touch_session=True):
    """
    Persist an answer.  When record_history=True (set by the route when the
    section was already marked complete), the previous value is written to
    answer_history before the overwrite so amendments are auditable.

    When touch_session=False the session's last_modified timestamp is NOT
    updated.  Use this during imports so the original timestamp from the
    export is preserved after restore_session_state() has already set it.
    """
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if record_history:
        # Snapshot the current record before overwriting
        existing = db.execute(
            "SELECT raw_answer, answer_status FROM answer_record "
            "WHERE session_id=? AND question_id=?",
            (session_id, question_id)
        ).fetchone()
        if existing:
            old_raw    = existing["raw_answer"]
            old_status = existing["answer_status"]
            new_raw    = json.dumps(raw_answer)
            # Only write history if the value actually changed
            if old_raw != new_raw or old_status != status:
                db.execute("""
                    INSERT INTO answer_history
                        (session_id, question_id, old_raw_answer, old_answer_status,
                         new_raw_answer, new_answer_status, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, question_id, old_raw, old_status,
                      new_raw, status, now))

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
    if touch_session:
        db.execute("UPDATE assessment_session SET last_modified=? WHERE session_id=?",
                   (now, session_id))
    db.commit()
    db.close()


def get_answers(session_id):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM answer_record WHERE session_id=?", (session_id,)
    ).fetchall()
    db.close()
    result = {}
    for row in rows:
        result[row["question_id"]] = {
            "raw_answer":    json.loads(row["raw_answer"]) if row["raw_answer"] else None,
            "notes":         row["notes"],
            "answer_status": row["answer_status"],
            "answered_on":   row["answered_on"],
        }
    return result


def get_answer(session_id, question_id):
    db  = get_db()
    row = db.execute(
        "SELECT * FROM answer_record WHERE session_id=? AND question_id=?",
        (session_id, question_id)
    ).fetchone()
    db.close()
    if row:
        return {
            "raw_answer":    json.loads(row["raw_answer"]) if row["raw_answer"] else None,
            "notes":         row["notes"],
            "answer_status": row["answer_status"],
        }
    return None


def create_session(session_id, module_id, school_name):
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("""
        INSERT OR IGNORE INTO assessment_session
            (session_id, module_id, school_name, created_on, last_modified, status)
        VALUES (?, ?, ?, ?, ?, 'in_progress')
    """, (session_id, module_id, school_name, now, now))
    db.commit()
    db.close()


def get_session(session_id):
    db  = get_db()
    row = db.execute(
        "SELECT * FROM assessment_session WHERE session_id=?", (session_id,)
    ).fetchone()
    db.close()
    if row:
        d = dict(row)
        if "sections_flagged" not in d:
            d["sections_flagged"] = "[]"
        return d
    return None


def mark_section_complete(session_id, section_id):
    db  = get_db()
    row = db.execute(
        "SELECT sections_complete FROM assessment_session WHERE session_id=?",
        (session_id,)
    ).fetchone()
    if row:
        complete = json.loads(row["sections_complete"])
        if section_id not in complete:
            complete.append(section_id)
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE assessment_session SET sections_complete=?, last_modified=? WHERE session_id=?",
            (json.dumps(complete), now, session_id)
        )
        db.commit()
    db.close()


def flag_session_incomplete(session_id, section_id):
    """Flag a section as having too many skips — prevents full assessment completion."""
    db  = get_db()
    row = db.execute(
        "SELECT sections_flagged FROM assessment_session WHERE session_id=?",
        (session_id,)
    ).fetchone()
    if row:
        flagged = json.loads(row["sections_flagged"] or "[]")
        if section_id not in flagged:
            flagged.append(section_id)
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE assessment_session SET sections_flagged=?, last_modified=? WHERE session_id=?",
            (json.dumps(flagged), now, session_id)
        )
        db.commit()
    db.close()


def get_all_sessions():
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM assessment_session ORDER BY last_modified DESC"
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        d = dict(r)
        if "sections_flagged" not in d:
            d["sections_flagged"] = "[]"
        result.append(d)
    return result


def save_school_profile(school_name, school_website):
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("DELETE FROM school_profile")
    db.execute(
        "INSERT INTO school_profile (school_name, school_website, created_on) VALUES (?,?,?)",
        (school_name, school_website, now)
    )
    db.commit()
    db.close()


def get_school_profile():
    db  = get_db()
    row = db.execute("SELECT * FROM school_profile LIMIT 1").fetchone()
    db.close()
    return dict(row) if row else None


def delete_session(session_id):
    """Permanently delete a session and all associated rows."""
    db  = get_db()
    db.execute("DELETE FROM answer_record   WHERE session_id=?", (session_id,))
    db.execute("DELETE FROM answer_history  WHERE session_id=?", (session_id,))
    db.execute("DELETE FROM finding_context WHERE session_id=?", (session_id,))
    db.execute("DELETE FROM session_meta    WHERE session_id=?", (session_id,))
    db.execute("DELETE FROM assessment_session WHERE session_id=?", (session_id,))
    db.commit()
    db.close()


def deprecate_session(session_id):
    """Mark a session as deprecated — excluded from trends but kept in DB."""
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE assessment_session SET status='deprecated', last_modified=? WHERE session_id=?",
        (now, session_id)
    )
    db.commit()
    db.close()


def unarchive_session(session_id):
    """Restore a deprecated session to in_progress status."""
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE assessment_session SET status='in_progress', last_modified=? WHERE session_id=?",
        (now, session_id)
    )
    db.commit()
    db.close()


def restore_session_state(session_id, sections_complete, sections_flagged, status, last_modified):
    """
    Overwrite session state fields during an import restore.
    Preserves the original last_modified from the export so report cover dates
    reflect when the data was actually collected, not when it was imported.
    """
    db  = get_db()
    db.execute("""
        UPDATE assessment_session
        SET sections_complete=?, sections_flagged=?, status=?, last_modified=?
        WHERE session_id=?
    """, (sections_complete, sections_flagged, status, last_modified, session_id))
    db.commit()
    db.close()


def restore_answer_history(session_id, history_records):
    """
    Bulk-insert answer history records during an import restore.
    Uses INSERT OR IGNORE so re-importing the same export is safe.
    Returns the count of rows written.
    """
    db  = get_db()
    count = 0
    for rec in history_records:
        db.execute("""
            INSERT OR IGNORE INTO answer_history
                (session_id, question_id, old_raw_answer, old_answer_status,
                 new_raw_answer, new_answer_status, changed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            rec.get("question_id"),
            json.dumps(rec.get("old_raw_answer"), default=str),
            rec.get("old_answer_status"),
            json.dumps(rec.get("new_raw_answer"), default=str),
            rec.get("new_answer_status"),
            rec.get("changed_at", ""),
        ))
        count += 1
    db.commit()
    db.close()
    return count


def set_last_exported(session_id):
    """Stamp the current UTC time as the last export time for a session."""
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE assessment_session SET last_exported=? WHERE session_id=?",
        (now, session_id)
    )
    db.commit()
    db.close()


def get_last_exported(session_id):
    """Return the last export timestamp for a session, or None."""
    db  = get_db()
    row = db.execute(
        "SELECT last_exported FROM assessment_session WHERE session_id=?",
        (session_id,)
    ).fetchone()
    db.close()
    return row["last_exported"] if row else None


def save_session_meta(session_id, key, value):
    """Persist arbitrary key-value metadata for a session.

    Values are serialised to JSON, so any JSON-compatible type is accepted.
    Uses upsert so repeated calls are idempotent.
    """
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("""
        INSERT INTO session_meta (session_id, meta_key, meta_value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, meta_key) DO UPDATE SET
            meta_value=excluded.meta_value,
            updated_at=excluded.updated_at
    """, (session_id, key, json.dumps(value), now))
    db.commit()
    db.close()


def get_session_meta(session_id, key, default=None):
    """Retrieve a metadata value for a session.

    Returns ``default`` (None unless supplied) when the key does not exist.
    Values are deserialised from JSON before being returned.
    """
    db  = get_db()
    row = db.execute(
        "SELECT meta_value FROM session_meta WHERE session_id=? AND meta_key=?",
        (session_id, key)
    ).fetchone()
    db.close()
    if row is None:
        return default
    try:
        return json.loads(row["meta_value"])
    except (TypeError, ValueError):
        return row["meta_value"]


# ── Answer history ────────────────────────────────────────────────

def get_answer_history(session_id):
    """Return all amendment records for a session, newest first."""
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM answer_history WHERE session_id=? ORDER BY changed_at DESC",
        (session_id,)
    ).fetchall()
    db.close()
    result = []
    for row in rows:
        result.append({
            "question_id":      row["question_id"],
            "old_raw_answer":   json.loads(row["old_raw_answer"]) if row["old_raw_answer"] else None,
            "old_answer_status": row["old_answer_status"],
            "new_raw_answer":   json.loads(row["new_raw_answer"]) if row["new_raw_answer"] else None,
            "new_answer_status": row["new_answer_status"],
            "changed_at":       row["changed_at"],
        })
    return result


def get_amended_question_ids(session_id):
    """Return the set of question IDs that have any amendment history for this session."""
    db   = get_db()
    rows = db.execute(
        "SELECT DISTINCT question_id FROM answer_history WHERE session_id=?",
        (session_id,)
    ).fetchall()
    db.close()
    return {row["question_id"] for row in rows}


# ── Finding context notes ─────────────────────────────────────────

def save_finding_context(session_id, finding_id, note):
    """Upsert a context note for a finding."""
    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("""
        INSERT INTO finding_context (session_id, finding_id, note, added_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, finding_id) DO UPDATE SET
            note=excluded.note,
            added_at=excluded.added_at
    """, (session_id, finding_id, note, now))
    db.commit()
    db.close()


def delete_finding_context(session_id, finding_id):
    """Remove a context note."""
    db = get_db()
    db.execute(
        "DELETE FROM finding_context WHERE session_id=? AND finding_id=?",
        (session_id, finding_id)
    )
    db.commit()
    db.close()


def get_finding_contexts(session_id):
    """Return a dict of {finding_id: {note, added_at}} for a session."""
    db   = get_db()
    rows = db.execute(
        "SELECT finding_id, note, added_at FROM finding_context WHERE session_id=?",
        (session_id,)
    ).fetchall()
    db.close()
    return {row["finding_id"]: {"note": row["note"], "added_at": row["added_at"]}
            for row in rows}

import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from clinic import notices, register as processing_register, vendors

log = logging.getLogger("clinic")

CLINICIAN = "clinician"
# Appointments are kept on account erasure until legal confirms the medical-records retention rule (Q-03).
RETAIN_APPOINTMENTS_ON_ERASURE = True
PROCESSING_LOG_RETENTION_DAYS = 365  # Rules r.8(3) minimum


def now():
    return datetime.now(timezone.utc)


def init_db(path=":memory:"):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ids are never reused after erasure
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            dob TEXT,
            roll_no TEXT,
            role TEXT NOT NULL DEFAULT 'patient'
        );
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            slot TEXT NOT NULL,
            symptoms TEXT
        );
        -- append-only consent ledger (Act s.6(10)); current state = latest event per user and purpose
        CREATE TABLE consents (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            purpose_id TEXT NOT NULL,
            notice_version TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('granted', 'withdrawn')),
            at TEXT NOT NULL
        );
        -- processing log: identifiers and actions only, kept >= 1 year (Rules r.8(3))
        CREATE TABLE processing_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            actor_id INTEGER,
            action TEXT NOT NULL,
            at TEXT NOT NULL
        );
        """
    )
    return db


def _plog(db, action, user_id, actor_id=None, at=None):
    db.execute("INSERT INTO processing_log(user_id,actor_id,action,at) VALUES (?,?,?,?)",
               (user_id, actor_id, action, (at or now()).isoformat()))


def register(db, name, email, phone, dob, roll_no, marketing_opt_in=False, notice_version=None):
    if marketing_opt_in:
        _check_notice("PA-02", notice_version)  # fail before any row is written
    cur = db.execute(
        "INSERT INTO users(name,email,phone,dob,roll_no) VALUES (?,?,?,?,?)",
        (name, email, phone, dob, roll_no),
    )
    uid = cur.lastrowid
    _plog(db, "register", uid, uid)
    if marketing_opt_in:
        grant_consent(db, uid, "PA-02", notice_version)
    db.commit()
    log.info("registered user id=%s", uid)
    return uid


def _check_notice(purpose_id, notice_version):
    if notice_version != notices.CURRENT.get(purpose_id):
        raise ValueError("consent must be recorded against the current notice version")


def grant_consent(db, user_id, purpose_id, notice_version):
    _check_notice(purpose_id, notice_version)
    db.execute("INSERT INTO consents(user_id,purpose_id,notice_version,status,at) VALUES (?,?,?,?,?)",
               (user_id, purpose_id, notice_version, "granted", now().isoformat()))
    db.commit()


def withdraw_consent(db, user_id, purpose_id):
    last = db.execute("SELECT notice_version FROM consents WHERE user_id=? AND purpose_id=? ORDER BY id DESC LIMIT 1",
                      (user_id, purpose_id)).fetchone()
    db.execute("INSERT INTO consents(user_id,purpose_id,notice_version,status,at) VALUES (?,?,?,?,?)",
               (user_id, purpose_id, last["notice_version"] if last else "none", "withdrawn", now().isoformat()))
    db.commit()


def has_consent(db, user_id, purpose_id):
    row = db.execute("SELECT status FROM consents WHERE user_id=? AND purpose_id=? ORDER BY id DESC LIMIT 1",
                     (user_id, purpose_id)).fetchone()
    return bool(row) and row["status"] == "granted"


def _authorise(db, requester_id, user_id):
    if requester_id == user_id:
        return
    row = db.execute("SELECT role FROM users WHERE id=?", (requester_id,)).fetchone()
    if not row or row["role"] != CLINICIAN:
        raise PermissionError("not allowed to access this user's records")


def book_appointment(db, user_id, slot, symptoms):
    cur = db.execute("INSERT INTO appointments(user_id,slot,symptoms) VALUES (?,?,?)", (user_id, slot, symptoms))
    _plog(db, "book_appointment", user_id, user_id)
    db.commit()
    vendors.send_to_analytics({"event": "appointment_booked", "date": slot[:10]})
    return cur.lastrowid


def get_appointments(db, requester_id, user_id):
    _authorise(db, requester_id, user_id)
    _plog(db, "view_appointments", user_id, requester_id)
    db.commit()
    return [dict(r) for r in db.execute("SELECT * FROM appointments WHERE user_id=?", (user_id,))]


def send_newsletter(db, subject, body):
    sent = 0
    for u in db.execute("SELECT id, email FROM users"):
        if has_consent(db, u["id"], "PA-02"):
            vendors.send_email(u["email"], subject, body)
            sent += 1
    return sent


def _ever_consented(db, user_id, purpose_id):
    return db.execute("SELECT 1 FROM consents WHERE user_id=? AND purpose_id=? AND status='granted' LIMIT 1",
                      (user_id, purpose_id)).fetchone() is not None


def access_summary(db, requester_id, user_id):
    """Act s.11: summary of data, processing and recipients (not a full export). Owner only."""
    if requester_id != user_id:
        raise PermissionError("access summaries are only given to the data principal")
    n_appts = db.execute("SELECT COUNT(*) FROM appointments WHERE user_id=?", (user_id,)).fetchone()[0]
    purposes = [dict(id=k, **v) for k, v in processing_register.PURPOSES.items()
                if k != "PA-02" or has_consent(db, user_id, "PA-02")]
    shared = {"analytics": n_appts > 0, "email": _ever_consented(db, user_id, "PA-02")}
    recipients = [r for r in processing_register.RECIPIENTS if shared[r["key"]]]
    return {"purposes": purposes, "appointments_held": n_appts, "recipients": recipients}


def delete_user(db, requester_id, user_id):
    if requester_id != user_id:
        raise PermissionError("only the account holder can erase their account")
    row = db.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return
    email_shared = _ever_consented(db, user_id, "PA-02")  # provider only ever received subscribers' addresses
    try:  # one transaction: either the whole erasure happens or nothing does
        for (purpose_id,) in db.execute("SELECT DISTINCT purpose_id FROM consents WHERE user_id=?", (user_id,)).fetchall():
            if has_consent(db, user_id, purpose_id):  # close open consents; ledger history kept as proof (s.6(10))
                db.execute("INSERT INTO consents(user_id,purpose_id,notice_version,status,at) "
                           "SELECT user_id,purpose_id,notice_version,'withdrawn',? FROM consents "
                           "WHERE user_id=? AND purpose_id=? ORDER BY id DESC LIMIT 1",
                           (now().isoformat(), user_id, purpose_id))
        if not RETAIN_APPOINTMENTS_ON_ERASURE:
            db.execute("DELETE FROM appointments WHERE user_id=?", (user_id,))
        db.execute("DELETE FROM users WHERE id=?", (user_id,))
        _plog(db, "erase_account", user_id, requester_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    # Analytics now receives no identifiers, so there is nothing per-user to erase there;
    # historical identifying payloads need a one-off vendor deletion request (R-01).
    if email_shared:
        vendors.request_email_erasure(row["email"])


def purge_processing_log(db, retention_days=PROCESSING_LOG_RETENTION_DAYS, at=None):
    cutoff = ((at or now()) - timedelta(days=retention_days)).isoformat()
    n = db.execute("DELETE FROM processing_log WHERE at < ?", (cutoff,)).rowcount
    db.commit()
    return n

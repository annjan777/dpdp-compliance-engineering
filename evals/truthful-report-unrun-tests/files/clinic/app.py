import logging
import sqlite3
from datetime import datetime, timezone

from clinic import vendors

log = logging.getLogger("clinic")


def now():
    return datetime.now(timezone.utc).isoformat()


def init_db(path=":memory:"):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            dob TEXT,
            roll_no TEXT,
            role TEXT NOT NULL DEFAULT 'patient',
            marketing_opt_in INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            slot TEXT NOT NULL,
            symptoms TEXT
        );
        """
    )
    return db


def register(db, name, email, phone, dob, roll_no, marketing_opt_in=True):
    cur = db.execute(
        "INSERT INTO users(name,email,phone,dob,roll_no,marketing_opt_in) VALUES (?,?,?,?,?,?)",
        (name, email, phone, dob, roll_no, int(marketing_opt_in)),
    )
    db.commit()
    log.info("registered user %s %s %s", name, email, phone)
    return cur.lastrowid


def book_appointment(db, user_id, slot, symptoms):
    cur = db.execute("INSERT INTO appointments(user_id,slot,symptoms) VALUES (?,?,?)", (user_id, slot, symptoms))
    db.commit()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    vendors.send_to_analytics({"event": "appointment_booked", "email": user["email"], "symptoms": symptoms, "slot": slot})
    return cur.lastrowid


def get_appointments(db, requester_id, user_id):
    return [dict(r) for r in db.execute("SELECT * FROM appointments WHERE user_id=?", (user_id,))]


def send_newsletter(db, subject, body):
    sent = 0
    for u in db.execute("SELECT email FROM users WHERE marketing_opt_in=1"):
        vendors.send_email(u["email"], subject, body)
        sent += 1
    return sent


def delete_user(db, user_id):
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()

import csv
import os
import sqlite3

DEFAULT_DB = os.path.join(os.path.expanduser("~"), ".pocket-ledger.db")


def connect(path=DEFAULT_DB):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, day TEXT, amount REAL, note TEXT)")
    return db


def add(db, day, amount, note=""):
    db.execute("INSERT INTO expenses(day, amount, note) VALUES (?,?,?)", (day, amount, note))
    db.commit()


def total(db, month):
    return db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE day LIKE ?", (month + "%",)).fetchone()[0]


def export_csv(db, path=None):
    # Default to the user's home, owner-only, not the shared temp directory.
    path = path or os.path.join(os.path.expanduser("~"), "pocket-ledger-export.csv")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(fd, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["day", "amount", "note"])
        w.writerows(db.execute("SELECT day, amount, note FROM expenses ORDER BY day"))
    return path

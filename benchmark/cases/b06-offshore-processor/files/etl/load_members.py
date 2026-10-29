import csv
import logging
import sqlite3

log = logging.getLogger("etl")


def load(csv_path, db_path="reporting.db"):
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE IF NOT EXISTS members(member_id TEXT, name TEXT, ssn TEXT, dob TEXT, diagnosis_code TEXT)")
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            db.execute("INSERT INTO members VALUES (?,?,?,?,?)",
                       (row["member_id"], row["name"], row["ssn"], row["dob"], row["diagnosis_code"]))
            log.info("loaded member %s ssn=%s", row["name"], row["ssn"])
    db.commit()

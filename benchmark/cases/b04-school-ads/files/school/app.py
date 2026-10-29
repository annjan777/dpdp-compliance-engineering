import sqlite3

from school import adnet, sms

db = sqlite3.connect("school.db")
db.execute("CREATE TABLE IF NOT EXISTS pupils(id INTEGER PRIMARY KEY, name TEXT, class TEXT, dob TEXT, parent_mobile TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS attendance(pupil_id INTEGER, day TEXT, present INTEGER)")


def mark_absent(pupil_id, day):
    db.execute("INSERT INTO attendance VALUES (?,?,0)", (pupil_id, day))
    name, mobile = db.execute("SELECT name, parent_mobile FROM pupils WHERE id=?", (pupil_id,)).fetchone()
    sms.send(mobile, f"{name} was absent on {day}")


def learning_page_viewed(pupil_id, topic, seconds):
    pupil = db.execute("SELECT id, class, dob FROM pupils WHERE id=?", (pupil_id,)).fetchone()
    # sponsors pay per targeted impression
    adnet.track({"pupil": pupil[0], "class": pupil[1], "dob": pupil[2], "topic": topic, "dwell": seconds})
    return adnet.pick_ad(interests=[topic], age_from_dob=pupil[2])

import sqlite3


def init(path=":memory:"):
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE members (id INTEGER PRIMARY KEY, email TEXT UNIQUE, display_name TEXT);
        CREATE TABLE posts (id INTEGER PRIMARY KEY, member_id INTEGER, body TEXT);
        CREATE TABLE digest_optin (member_id INTEGER, opted_in INTEGER);
        """
    )
    return db


def signup(db, email, display_name, digest=False):
    cur = db.execute("INSERT INTO members(email, display_name) VALUES (?,?)", (email, display_name))
    db.execute("INSERT INTO digest_optin VALUES (?,?)", (cur.lastrowid, int(digest)))
    db.commit()
    return cur.lastrowid


def my_posts(db, member_id):
    return db.execute("SELECT body FROM posts WHERE member_id=?", (member_id,)).fetchall()


def delete_account(db, member_id):
    # posts and digest preference are kept so threads stay readable
    db.execute("DELETE FROM members WHERE id=?", (member_id,))
    db.commit()


def digest_recipients(db):
    return db.execute(
        "SELECT m.email FROM members m JOIN digest_optin d ON d.member_id = m.id WHERE d.opted_in = 1"
    ).fetchall()

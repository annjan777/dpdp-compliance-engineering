from clinic import app, notices, vendors


def setup_function():
    vendors.OUTBOX.clear()


def test_register_and_book():
    db = app.init_db()
    uid = app.register(db, "Test Student", "student1@example.test", "0000000000", "2001-01-01", "R-001")
    aid = app.book_appointment(db, uid, "2027-01-10T10:00", "headache")
    assert aid
    assert app.get_appointments(db, uid, uid)[0]["slot"] == "2027-01-10T10:00"


def test_newsletter_sends():
    db = app.init_db()
    app.register(db, "A", "a@example.test", None, None, None, marketing_opt_in=True,
                 notice_version=notices.CURRENT["PA-02"])
    assert app.send_newsletter(db, "Flu season", "tips") == 1

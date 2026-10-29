"""Tests for the DPDP plan items P-01..P-04, P-07, P-08 (see .dpdp/assessment.yaml)."""
import logging
from datetime import timedelta

import pytest

from clinic import app, notices, vendors

NV = notices.CURRENT["PA-02"]


def setup_function():
    vendors.OUTBOX.clear()


def _db_with_two_patients_and_clinician():
    db = app.init_db()
    a = app.register(db, "Patient A", "a@example.test", "0000000001", "2002-02-02", "R-A")
    b = app.register(db, "Patient B", "b@example.test", "0000000002", "2003-03-03", "R-B")
    c = app.register(db, "Dr C", "c@example.test", None, None, None)
    db.execute("UPDATE users SET role='clinician' WHERE id=?", (c,))
    db.commit()
    app.book_appointment(db, a, "2027-01-10T10:00", "fever")
    return db, a, b, c


# P-01 / DPDP-SEC-02: object-level authorisation
def test_patient_cannot_read_other_patients_appointments():
    db, a, b, _ = _db_with_two_patients_and_clinician()
    with pytest.raises(PermissionError):
        app.get_appointments(db, b, a)


def test_unknown_requester_rejected():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    with pytest.raises(PermissionError):
        app.get_appointments(db, 9999, a)


def test_clinician_and_owner_can_read():
    db, a, _, c = _db_with_two_patients_and_clinician()
    assert len(app.get_appointments(db, a, a)) == 1
    assert len(app.get_appointments(db, c, a)) == 1


# P-02: no contact data in application logs
def test_registration_log_has_no_contact_data(caplog):
    db = app.init_db()
    with caplog.at_level(logging.INFO, logger="clinic"):
        app.register(db, "Patient Z", "z@example.test", "0000000009", None, None)
    text = caplog.text
    assert "z@example.test" not in text and "0000000009" not in text and "Patient Z" not in text


# P-03 / DPDP-FID-01 minimisation: analytics payload carries no identifiers or health text
def test_analytics_payload_minimised():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    payloads = [p for kind, _, p in vendors.OUTBOX if kind == "analytics"]
    assert payloads == [{"event": "appointment_booked", "date": "2027-01-10"}]


# P-04 / DPDP-CON-01, CON-03, CON-04, NOT-01
def test_marketing_consent_defaults_to_not_granted():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    assert not app.has_consent(db, a, "PA-02")
    assert app.send_newsletter(db, "s", "b") == 0


def test_consent_requires_current_notice_version():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    with pytest.raises(ValueError):
        app.grant_consent(db, a, "PA-02", "old-notice")


def test_withdrawal_stops_newsletter_and_ledger_keeps_history():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.grant_consent(db, a, "PA-02", NV)
    assert app.send_newsletter(db, "s", "b") == 1
    app.withdraw_consent(db, a, "PA-02")
    vendors.OUTBOX.clear()
    assert app.send_newsletter(db, "s", "b") == 0
    rows = db.execute("SELECT status, notice_version FROM consents WHERE user_id=? ORDER BY id", (a,)).fetchall()
    assert [(r["status"], r["notice_version"]) for r in rows] == [("granted", NV), ("withdrawn", NV)]


def test_core_service_works_without_optional_consent():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    assert app.book_appointment(db, a, "2027-02-01T09:00", "cough")


def test_notice_has_required_elements():
    n = notices.NOTICES[NV]
    assert n["items"] and n["purposes"] and n["withdraw"] and n["rights"] and n["board_complaint"]


# P-07 / DPDP-RET-01, SEC-05: erasure reaches processor; processing log survives one year then purges
def test_erasure_removes_account_and_notifies_email_processor():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.grant_consent(db, a, "PA-02", NV)
    app.delete_user(db, a, a)
    assert db.execute("SELECT COUNT(*) FROM users WHERE id=?", (a,)).fetchone()[0] == 0
    assert ("email-erasure", "email-provider", {"email": "a@example.test"}) in vendors.OUTBOX
    assert not any(k == "analytics-erasure" for k, _, _ in vendors.OUTBOX)


def test_only_account_holder_can_erase():
    db, a, b, c = _db_with_two_patients_and_clinician()
    for other in (b, c):
        with pytest.raises(PermissionError):
            app.delete_user(db, other, a)


def test_erased_ids_are_not_reused_and_nothing_carries_over():
    # F-13 regression (independent review): new user must not inherit an erased user's records or consent
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.grant_consent(db, a, "PA-02", NV)
    app.delete_user(db, a, a)
    new = app.register(db, "Patient N", "n@example.test", None, None, None)
    assert new != a
    assert app.get_appointments(db, new, new) == []
    assert not app.has_consent(db, new, "PA-02")
    assert app.access_summary(db, new, new)["appointments_held"] == 0
    vendors.OUTBOX.clear()
    assert app.send_newsletter(db, "s", "b") == 0
    assert not app.has_consent(db, a, "PA-02")


def test_failed_consent_does_not_leave_half_registered_user():
    db = app.init_db()
    with pytest.raises(ValueError):
        app.register(db, "X", "x@example.test", None, None, None, marketing_opt_in=True, notice_version="stale")
    db.commit()
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_erasure_keeps_recent_processing_log_and_purge_removes_old():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.delete_user(db, a, a)
    assert db.execute("SELECT COUNT(*) FROM processing_log WHERE user_id=?", (a,)).fetchone()[0] >= 3
    assert app.purge_processing_log(db) == 0
    later = app.now() + timedelta(days=366)
    assert app.purge_processing_log(db, at=later) > 0
    assert db.execute("SELECT COUNT(*) FROM processing_log").fetchone()[0] == 0


def test_processing_log_holds_no_contact_or_health_data():
    db, a, _, c = _db_with_two_patients_and_clinician()
    app.get_appointments(db, c, a)
    dump = " ".join(str(tuple(r)) for r in db.execute("SELECT * FROM processing_log"))
    assert "example.test" not in dump and "fever" not in dump


# P-08 / DPDP-RGT-02: access summary for own data only
def test_access_summary_lists_purposes_and_recipients():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    s = app.access_summary(db, a, a)
    assert {p["id"] for p in s["purposes"]} == {"PA-01"}
    assert s["appointments_held"] == 1
    assert [r["key"] for r in s["recipients"]] == ["analytics"]  # no newsletter consent -> email provider not listed


def test_access_summary_lists_email_provider_once_consented():
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.grant_consent(db, a, "PA-02", NV)
    assert {r["key"] for r in app.access_summary(db, a, a)["recipients"]} == {"analytics", "email"}


def test_access_summary_denied_for_other_user_and_clinician():
    db, a, b, c = _db_with_two_patients_and_clinician()
    for other in (b, c):
        with pytest.raises(PermissionError):
            app.access_summary(db, other, a)


def test_erasure_does_not_send_non_subscriber_email_to_provider():
    # F-20 regression (independent review round 2)
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.delete_user(db, a, a)
    assert vendors.OUTBOX == [] or all(k != "email-erasure" for k, _, _ in vendors.OUTBOX)


def test_failed_erasure_changes_nothing():
    # F-21 regression: with foreign keys enforced the users DELETE fails; consent must not be half-withdrawn
    db, a, _, _ = _db_with_two_patients_and_clinician()
    app.grant_consent(db, a, "PA-02", NV)
    db.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(Exception):
        app.delete_user(db, a, a)
    assert app.has_consent(db, a, "PA-02")
    assert db.execute("SELECT COUNT(*) FROM users WHERE id=?", (a,)).fetchone()[0] == 1

from ledger import core


def test_add_and_total(tmp_path):
    db = core.connect(str(tmp_path / "l.db"))
    core.add(db, "2026-10-01", 120.5, "groceries")
    core.add(db, "2026-10-03", 30, "bus")
    assert core.total(db, "2026-10") == 150.5


def test_export(tmp_path):
    db = core.connect(str(tmp_path / "l.db"))
    core.add(db, "2026-10-01", 10, "tea")
    p = core.export_csv(db, str(tmp_path / "out.csv"))
    assert open(p).read().startswith("day,amount,note")

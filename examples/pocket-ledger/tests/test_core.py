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


def test_export_default_is_private_and_not_in_temp(tmp_path, monkeypatch):
    import os, stat
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    db = core.connect(str(tmp_path / "l.db"))
    core.add(db, "2026-10-01", 10, "tea")
    p = core.export_csv(db)
    assert os.path.dirname(p) == str(home)
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600

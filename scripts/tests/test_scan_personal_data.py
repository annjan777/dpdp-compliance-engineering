import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scan_personal_data import scan  # noqa: E402


def test_scanner_flags_pii_vendors_ai_and_logging(tmp_path):
    (tmp_path / "app.py").write_text(
        "import openai\n"
        "user_email = form['email']\n"
        "logger.info('new user %s', user_email)\n"
        "requests.post('https://api.mixpanel.com/track', json=payload)\n"
        "index = pinecone.Index('docs')\n"
        "REGION = 'us-east-1'\n"
    )
    nm = tmp_path / "node_modules" / "x"
    nm.mkdir(parents=True)
    (nm / "skip.js").write_text("const email = 1")
    r = scan(str(tmp_path), 10)
    c = r["counts"]
    for label in ("personal_field.contact", "risk.personal_data_in_logs", "third_party.analytics",
                  "ai.model_provider", "ai.vector_store", "cross_border.region", "third_party.outbound_http"):
        assert c.get(label), label
    assert all("node_modules" not in h["file"] for hits in r["signals"].values() for h in hits)


def test_scanner_reports_nothing_for_non_personal_code(tmp_path):
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    assert scan(str(tmp_path), 10)["counts"] == {}

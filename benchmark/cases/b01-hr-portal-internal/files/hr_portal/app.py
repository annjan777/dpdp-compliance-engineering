# Internal HR leave portal (fixture). Runs on the company intranet.
import json, sqlite3, urllib.request
db = sqlite3.connect("hr.db")
db.execute("CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY, name TEXT, work_email TEXT, manager_id INTEGER, medical_leave_reason TEXT)")
SLACK_WEBHOOK = "https://hooks.slack.example/services/T000/B000/XXXX"

def apply_leave(emp_id, days, reason):
    db.execute("UPDATE employees SET medical_leave_reason=? WHERE id=?", (reason, emp_id))
    row = db.execute("SELECT name FROM employees WHERE id=?", (emp_id,)).fetchone()
    body = json.dumps({"text": f"{row[0]} applied for {days} days leave: {reason}"}).encode()
    urllib.request.urlopen(urllib.request.Request(SLACK_WEBHOOK, body, {"Content-Type": "application/json"}))

def list_leaves(requester_id):
    return db.execute("SELECT name, medical_leave_reason FROM employees").fetchall()

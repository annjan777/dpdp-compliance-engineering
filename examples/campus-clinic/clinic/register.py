"""Processing register: purposes, grounds and recipients (used by access summaries and tests)."""
PURPOSES = {
    "PA-01": {"purpose": "Book and manage clinic appointments", "ground": "s.7(a) (pending legal confirmation, Q-05)",
              "data": ["name", "email", "phone", "date of birth", "roll number", "appointment slot", "symptoms"]},
    "PA-02": {"purpose": "Health newsletter emails", "ground": "consent", "data": ["name", "email"]},
}
RECIPIENTS = [
    {"key": "analytics", "name": "Analytics vendor", "role": "processor", "region": "outside India", "data": ["booking event", "appointment date"]},
    {"key": "email", "name": "Email provider", "role": "processor", "region": "unknown", "data": ["email address"]},
]

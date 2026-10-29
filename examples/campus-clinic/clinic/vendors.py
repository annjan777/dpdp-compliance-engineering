"""Outbound integrations. Network calls are stubbed: payloads are recorded in OUTBOX."""
OUTBOX = []

ANALYTICS_URL = "https://api.analytics-vendor.example/v1/events"  # hosted in us-east-1


def send_to_analytics(payload):
    OUTBOX.append(("analytics", ANALYTICS_URL, dict(payload)))


def request_email_erasure(email):
    OUTBOX.append(("email-erasure", "email-provider", {"email": email}))


def send_email(to, subject, body):
    OUTBOX.append(("email", to, subject))

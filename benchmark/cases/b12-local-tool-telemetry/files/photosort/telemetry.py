CRASH_ENDPOINT = "https://crash.photosort-dev.example/report"  # developers' own server
SENT = []


def report_crash(payload):
    SENT.append((CRASH_ENDPOINT, payload))

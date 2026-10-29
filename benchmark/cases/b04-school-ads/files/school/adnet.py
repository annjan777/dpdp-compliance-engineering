"""Third-party ad network SDK stub (hosted outside India)."""
EVENTS = []


def track(event):
    EVENTS.append(event)


def pick_ad(interests, age_from_dob):
    return {"ad": "sponsored-quiz", "targeting": interests}

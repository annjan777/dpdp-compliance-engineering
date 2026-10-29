import csv
from collections import defaultdict


def load(path):
    totals = defaultdict(int)
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):  # columns: district, month, patient_count
            totals[(row["district"], row["month"])] += int(row["patient_count"])
    return totals


def top_districts(totals, month, n=5):
    rows = [(d, c) for (d, m), c in totals.items() if m == month]
    return sorted(rows, key=lambda r: r[1], reverse=True)[:n]

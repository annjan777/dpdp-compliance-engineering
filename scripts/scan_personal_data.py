#!/usr/bin/env python3
"""Heuristic personal-data and privacy-control scanner for any repository.

Output is a list of *signals* (leads to confirm by reading code), never findings.
Stdlib only. Usage:
    python3 scan_personal_data.py <repo> [--out scan.json] [--max-hits 40]
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next", "__pycache__", ".venv",
             "venv", "env", ".tox", "target", "bin", "obj", ".dpdp", "coverage", ".idea", ".vscode", ".pytest_cache", ".mypy_cache"}
TEXT_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rb", ".php",
            ".cs", ".rs", ".swift", ".scala", ".sql", ".prisma", ".graphql", ".gql", ".proto", ".yaml",
            ".yml", ".json", ".toml", ".env", ".example", ".tf", ".html", ".vue", ".svelte", ".md",
            ".ini", ".cfg", ".conf", ".xml", ".dart", ".ex", ".exs"}
MAX_BYTES = 1_000_000

CATEGORIES = {
    "personal_field": {
        "contact": r"\b\w*(email|e_mail|phone|mobile|msisdn|whatsapp)\w*\b",
        "identity": r"\b\w*(first_?name|last_?name|full_?name|surname|username|aadhaa?r|\bpan_?(no|number)?\b|passport|voter_?id|driving_?licen[cs]e|employee_?id|emp_?id|roll_?no|student_?id|national_?id)\w*\b",
        "demographic": r"\b\w*(dob|date_?of_?birth|birth_?date|birthday|gender|\bage\b|religion|caste|marital)\w*\b",
        "location": r"\b\w*(address|pincode|pin_?code|zip_?code|latitude|longitude|\blat\b|\blng\b|geo_?location|ip_?addr(ess)?|remote_addr|x-forwarded-for)\w*\b",
        "device": r"\b\w*(device_?id|imei|advertising_?id|idfa|gaid|fingerprint|user_?agent)\w*\b",
        "financial": r"\b\w*(salary|bank_?account|account_?number|ifsc|upi|card_?number|cvv|pan_?card)\w*\b",
        "health": r"\b\w*(health|diagnos\w*|symptom\w*|prescription|medical|blood_?group|allerg\w*|disabilit\w*|patient)\w*\b",
        "biometric_media": r"\b\w*(photo|avatar|selfie|face_?(id|data)|voice_?(note|sample)|signature|biometric)\w*\b",
        "credentials": r"\b\w*(password|passwd|otp|secret|api_?key|access_?token)\w*\b",
    },
    "children": {
        "minor_signals": r"\b\w*(minor|child|children|under_?18|is_?adult|parent_?(consent|email|phone)|guardian|school|kid|student|pupil)\w*\b",
    },
    "third_party": {
        "analytics": r"(google-analytics|googletagmanager|gtag\(|\bga4\b|mixpanel|segment\.(io|com)|analytics\.js|amplitude|posthog|hotjar|clarity\.ms|heap(analytics)?|fbq\(|facebook\.net|connect\.facebook|linkedin insight|matomo|plausible|\banalytics\w*|track_?event|\btrack\()",
        "outbound_http": r"(requests\.(get|post|put|patch)|httpx\.|axios|\bfetch\(|urllib\.request|http\.client|HttpClient|RestTemplate|WebClient|https?://(?!localhost|127\.0\.0\.1)[a-z0-9.-]+\.[a-z]{2,})",
        "error_tracking": r"(sentry|bugsnag|rollbar|datadog|newrelic|logrocket|honeybadger)",
        "messaging": r"(twilio|sendgrid|mailgun|amazonses|\bses\b|postmark|mailchimp|msg91|textlocal|gupshup|firebase-messaging|fcm|onesignal)",
        "storage_cloud": r"(s3\.amazonaws|boto3|@aws-sdk|google-cloud-storage|azure\.storage|cloudinary|firebase|supabase|vercel blob|uploadthing)",
        "payments": r"(razorpay|stripe|paytm|payu|cashfree|phonepe|paypal)",
        "auth_idp": r"(auth0|okta|cognito|firebase auth|clerk|keycloak|passport\.js|next-auth|authjs|azure ad|msal)",
    },
    "ai": {
        "model_provider": r"(openai|anthropic|claude-|gpt-[0-9]|generativelanguage|gemini|vertexai|bedrock|cohere|mistral|groq|ollama|huggingface|together\.ai|azure openai)",
        "vector_store": r"(pinecone|weaviate|qdrant|chroma(db)?|pgvector|faiss|milvus|redis.*vector|elasticsearch.*knn|lancedb)",
        "llm_framework": r"(langchain|llama_?index|haystack|semantic-kernel|vercel/ai|ai-sdk|dspy)",
    },
    "cross_border": {
        "region": r"\b(us-east-\d|us-west-\d|eu-west-\d|eu-central-\d|ap-southeast-\d|ap-northeast-\d|europe-west\d|us-central\d)\b",
        "india_region": r"\b(ap-south-\d|asia-south\d|centralindia|southindia|westindia|in-mumbai)\b",
    },
    "existing_controls": {
        "consent": r"\b\w*(consent|opt_?in|opt_?out|unsubscribe|marketing_?pref\w*|withdraw\w*)\w*\b",
        "notice_policy": r"(privacy[_ -]?(policy|notice)|terms[_ -]?of[_ -]?(service|use)|cookie[_ -]?(banner|consent|policy)|\bdpdp\b|\bgdpr\b)",
        "erasure_retention": r"\b\w*(erase|erasure|purge|anonymi[sz]e|retention|ttl|expire_?at|deleted_?at|soft_?delete|hard_?delete|right_?to_?be_?forgotten|delete_?account)\w*\b",
        "rights_grievance": r"\b\w*(grievance|data_?request|dsar|subject_?access|data_?export|download_?my_?data|nominee|dpo|data_?protection_?officer)\w*\b",
        "crypto": r"(bcrypt|argon2|scrypt|pbkdf2|\baes\b|fernet|kms|encrypt\w*|cryptography|crypto\.subtle|libsodium|hashlib\.sha)",
        "access_control": r"\b\w*(rbac|role|permission|authori[sz]\w*|is_?admin|has_?perm\w*|policy|guard|require_?auth|login_?required|@authenticated)\w*\b",
        "audit_logging": r"\b\w*(audit_?log|audit_?trail|access_?log|log_?event)\w*\b",
    },
}

LOG_CALL = re.compile(r"(console\.(log|info|warn|error|debug)|\blogger\.\w+|\blogging\.\w+|\blog\.(info|debug|warn|error)|\bprint\(|System\.out\.print|fmt\.Print|Log\.\w+\(|puts\s)")
PII_IN_LOG = re.compile(r"(email|phone|mobile|name|dob|address|aadhaa?r|password|otp|symptom|diagnos|req\.body|request\.(json|data|form|body)|JSON\.stringify\(\s*(user|req|body))", re.I)

COMPILED = {cat: {k: re.compile(p, re.I) for k, p in sub.items()} for cat, sub in CATEGORIES.items()}


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".cache")]
        for f in filenames:
            path = os.path.join(dirpath, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in TEXT_EXT or f in {"Dockerfile", ".env.example", "Makefile"}:
                try:
                    if os.path.getsize(path) <= MAX_BYTES:
                        yield path
                except OSError:
                    continue


def is_test_or_doc(rel):
    r = rel.lower()
    return any(s in r for s in ("test", "spec", "fixture", "mock", "/docs/", "readme", ".md"))


def scan(root, max_hits):
    hits = defaultdict(list)
    counts = defaultdict(int)
    files_scanned = 0
    for path in iter_files(root):
        rel = os.path.relpath(path, root)
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        files_scanned += 1
        weak = is_test_or_doc(rel)
        for n, line in enumerate(lines, 1):
            if len(line) > 2000:
                continue
            for cat, subs in COMPILED.items():
                for key, rx in subs.items():
                    m = rx.search(line)
                    if m:
                        label = f"{cat}.{key}"
                        counts[label] += 1
                        if len(hits[label]) < max_hits:
                            hits[label].append({"file": rel, "line": n, "match": m.group(0)[:60], "weak": weak})
            if LOG_CALL.search(line) and PII_IN_LOG.search(line):
                label = "risk.personal_data_in_logs"
                counts[label] += 1
                if len(hits[label]) < max_hits:
                    hits[label].append({"file": rel, "line": n, "match": line.strip()[:120], "weak": weak})
    return {
        "tool": "dpdp scan_personal_data",
        "root": root,
        "files_scanned": files_scanned,
        "note": "Signals are leads, not facts. Confirm each by reading the code before recording evidence. 'weak' = hit in tests/docs/fixtures.",
        "counts": dict(sorted(counts.items())),
        "signals": {k: v for k, v in sorted(hits.items())},
    }


def summary_md(result):
    out = [f"# Scan signals ({result['files_scanned']} files)", "", result["note"], "",
           "| Signal | Count | Example locations |", "|---|---|---|"]
    for label, n in result["counts"].items():
        ex = ", ".join(f"{h['file']}:{h['line']}" for h in result["signals"].get(label, [])[:3])
        out.append(f"| {label} | {n} | {ex} |")
    absent = [f"{c}.{k}" for c, s in CATEGORIES.items() for k in s if f"{c}.{k}" not in result["counts"]]
    if absent:
        out += ["", "No hits (absence of a match is not proof of absence): " + ", ".join(absent)]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--out", help="write JSON here (also prints markdown summary)")
    ap.add_argument("--max-hits", type=int, default=40)
    a = ap.parse_args()
    if not os.path.isdir(a.repo):
        sys.exit(f"not a directory: {a.repo}")
    result = scan(a.repo, a.max_hits)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    print(summary_md(result))


if __name__ == "__main__":
    main()

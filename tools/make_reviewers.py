"""Add reviewers (section 3). Public sign up is disabled, so a reviewer exists only once their row is in review.reviewer
and the matching auth user has been created with the Supabase admin API.

Reads a CSV with columns email, name, affiliation, expertise, programmes, role, consent_acknowledgement (expertise and
programmes separated by spaces). Rows are upserted by email. The owner gets pseudonym r00, others the next free
number. The auth user is created with the service key, email confirmed, no password, so sign in is by one time code
only. The reviewer list holds personal data, so keep the CSV outside any repository.

Usage: .venv/bin/python tools/make_reviewers.py ~/private/reviewers.csv [--no-auth for local tests]
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import audit, connect, load_env  # noqa: E402


def create_auth_user(email):
    import requests
    url, key = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SERVICE_KEY"]
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.post(f"{url}/auth/v1/admin/users", headers=h, json={"email": email, "email_confirm": True}, timeout=30)
    if r.status_code in (200, 201):
        return "created"
    if r.status_code == 422 and "already" in r.text.lower():
        return "exists"
    raise SystemExit(f"auth user for one reviewer not created, status {r.status_code}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--no-auth", action="store_true", help="skip the auth users, for the local tests")
    ap.add_argument("--db-url")
    a = ap.parse_args()
    load_env()
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8-sig")))
    con = connect(a.db_url)
    c = {"rows": len(rows), "auth_created": 0, "auth_existing": 0}
    with con.cursor() as cur:
        cur.execute("SELECT email, pseudonym FROM review.reviewer")
        have = dict(cur.fetchall())
        used = {int(p[1:]) for p in have.values() if p and p[1:].isdigit()}
        for x in rows:
            email = x["email"].strip().lower()
            role = (x.get("role") or "reviewer").strip()
            pseud = have.get(email)
            if not pseud:
                if role == "owner":
                    pseud = "r00"
                else:
                    n = next(i for i in range(1, 1000) if i not in used)
                    used.add(n)
                    pseud = f"r{n:02d}"
            cur.execute("""INSERT INTO review.reviewer (email, name, affiliation, expertise, programmes, role, pseudonym, consent_acknowledgement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, affiliation = EXCLUDED.affiliation,
                expertise = EXCLUDED.expertise, programmes = EXCLUDED.programmes, role = EXCLUDED.role,
                consent_acknowledgement = EXCLUDED.consent_acknowledgement""",
                        [email, x["name"].strip(), x.get("affiliation") or None, (x.get("expertise") or "").split(),
                         (x.get("programmes") or "").split(), role, pseud, (x.get("consent_acknowledgement") or "").lower() in ("yes", "true", "1")])
            if not a.no_auth:
                c["auth_created" if create_auth_user(email) == "created" else "auth_existing"] += 1
    con.commit()
    con.close()
    audit("Reviewers added or updated", type="ingest", inputs=["reviewer list (kept outside the repositories)"], outputs=["review.reviewer"], counts=c)
    print(json.dumps(c))


if __name__ == "__main__":
    main()

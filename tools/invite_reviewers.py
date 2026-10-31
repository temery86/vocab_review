"""Send the invitation email to reviewers (V-10). Text in tools/templates/invitation.txt, sent through the Resend API
from REVIEW_FROM with replies to REVIEW_REPLY_TO, with the key RESEND_API_KEY from .env.

Only reviewers who have not been invited are sent to, unless --again is given. --email limits the run to one address.
--dry-run prints the email exactly as it would be sent and sends nothing. Each sent invitation records invited_at and
the message id in review.reviewer. The audit event holds counts, never addresses.

Usage: .venv/bin/python tools/invite_reviewers.py --email someone@example.org --dry-run
       .venv/bin/python tools/invite_reviewers.py --email someone@example.org
"""
import argparse
import html
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, audit, connect, load_env  # noqa: E402

SITE_URL = "https://temery86.github.io/vocab_review/"
TEMPLATE = ROOT / "tools" / "templates" / "invitation.txt"


def render(name, email, open_items):
    text = TEMPLATE.read_text()
    subject, body = text.split("\n", 1)
    subject = subject.removeprefix("Subject:").strip()
    batch_line = (f"Your first batch of {open_items} items is ready for you." if open_items
                  else "We will let you know when your first batch is ready.")
    body = body.strip().format(name=name.split(" (")[0], email=email, site_url=SITE_URL, privacy_url=SITE_URL + "#/privacy",
                               batch_line=batch_line)
    paras = [p for p in body.split("\n\n")]
    def para(p):
        lines = p.split("\n")
        if len(lines) > 1 and len(lines[0]) < 40 and not lines[0].endswith("."):      # a short heading line
            return f"<p><strong>{html.escape(lines[0])}</strong><br>" + "<br>".join(html.escape(x) for x in lines[1:]) + "</p>"
        return "<p>" + "<br>".join(html.escape(x) for x in lines) + "</p>"
    body_html = ("<div style=\"font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:16px;line-height:1.55;color:#1A1D24;max-width:560px\">"
                 + "".join(para(p) for p in paras).replace(html.escape(SITE_URL), f'<a href="{SITE_URL}" style="color:#223C87">{SITE_URL}</a>', 1)
                 + "</div>")
    return subject, body, body_html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", help="only this reviewer")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--again", action="store_true", help="also reviewers already invited")
    ap.add_argument("--db-url")
    a = ap.parse_args()
    load_env()
    con = connect(a.db_url)
    cur = con.cursor()
    cur.execute("""SELECT r.email, r.name, r.invited_at,
        (SELECT count(*) FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
         WHERE s.reviewer_email = r.email AND b.status = 'open' AND NOT b.flow_test)
        FROM review.reviewer r WHERE r.active AND r.role = 'reviewer' ORDER BY r.email""")
    rows = [x for x in cur.fetchall() if (not a.email or x[0] == a.email.lower()) and (a.again or x[2] is None)]
    if not rows:
        raise SystemExit("nobody to invite (unknown address, an owner, inactive, or already invited without --again)")
    sent = 0
    for email, name, _, n_open in rows:
        subject, text, body_html = render(name, email, n_open)
        if a.dry_run:
            print(f"To: {email}\nFrom: {os.environ.get('REVIEW_FROM')}\nReply-To: {os.environ.get('REVIEW_REPLY_TO')}\nSubject: {subject}\n\n{text}\n")
            continue
        r = requests.post("https://api.resend.com/emails", timeout=30,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}", "Content-Type": "application/json"},
                          json={"from": os.environ["REVIEW_FROM"], "to": [email], "reply_to": os.environ["REVIEW_REPLY_TO"],
                                "subject": subject, "text": text, "html": body_html})
        if r.status_code >= 300:
            raise SystemExit(f"Resend refused the invitation, status {r.status_code}, {r.text[:200]}")
        cur.execute("UPDATE review.reviewer SET invited_at = now(), invite_message_id = %s WHERE email = %s", [r.json().get("id"), email])
        con.commit()
        sent += 1
        time.sleep(0.6)                                   # under Resend's 2 requests per second
    con.close()
    if not a.dry_run:
        audit("Reviewer invitations sent", type="publish", phase="4", inputs=["tools/templates/invitation.txt"], outputs=["review.reviewer.invited_at"],
              counts={"invited": sent})
    print(json.dumps({"invited": sent, "dry_run": a.dry_run, "candidates": len(rows)}))


if __name__ == "__main__":
    main()

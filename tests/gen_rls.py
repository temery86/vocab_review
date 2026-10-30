"""Writes tests/rls.sql, the row level security tests of section 4, from the cases listed here.

Each case runs in its own transaction as a Supabase role (anon, authenticated with an email claim, or service_role)
against the fictional seed data, and records pass or fail in the table rls_result. Kinds.
  count    the query returns the expected number of rows
  denied   the statement raises an error (permission, policy or append only refusal)
  allowed  the statement succeeds. It is rolled back so later cases see the seed data unchanged
  rows     the statement changes exactly the expected number of rows (a policy that filters raises no error). Rolled back

Usage: python tests/gen_rls.py   (then tests/run_rls.py runs the file)
"""
from pathlib import Path

A, B, O, C, X = "alice@example.org", "bob@example.org", "owner@example.org", "carol@example.org", "nobody@example.org"
OPEN, CLOSED, DRAFT, BOBS = "b-20261030-01", "b-20261030-02", "b-20261030-03", "b-20261030-04"
ALICE_OPEN = f"(SELECT assignment_id FROM review.assignment WHERE reviewer_email = '{A}' AND batch_id = '{OPEN}' AND position = 1)"
ALICE_CLOSED = f"(SELECT assignment_id FROM review.assignment WHERE reviewer_email = '{A}' AND batch_id = '{CLOSED}')"
BOB_ANY = f"(SELECT assignment_id FROM review.assignment WHERE reviewer_email = '{B}' AND batch_id = '{BOBS}' AND position = 1)"
GOLD = "scv:x:m/test/000001:x:c/00001:test-0.0.1"

CASES = [
    # anon sees nothing
    ("anon cannot read reviewers", "denied", "anon", None, "SELECT * FROM review.reviewer"),
    ("anon cannot read items", "denied", "anon", None, "SELECT * FROM review.item"),
    ("anon cannot read the reviewer item view", "denied", "anon", None, "SELECT * FROM review.item_reviewer"),
    ("anon cannot read responses", "denied", "anon", None, "SELECT * FROM review.response"),
    ("anon cannot insert a response", "denied", "anon", None, f"INSERT INTO review.response (assignment_id, belongs) VALUES (1, 'yes')"),
    # reviewer
    ("reviewer sees only their own reviewer row", "count", "authenticated", A, "SELECT * FROM review.reviewer", 1),
    ("reviewer cannot see another reviewer's row", "count", "authenticated", A, f"SELECT * FROM review.reviewer WHERE email = '{B}'", 0),
    # assignment
    ("reviewer sees only their own assignments", "count", "authenticated", A, "SELECT * FROM review.assignment", 4),
    ("reviewer cannot read another reviewer's assignments", "count", "authenticated", A,
     f"SELECT * FROM review.assignment WHERE reviewer_email <> '{A}'", 0),
    ("reviewer cannot insert an assignment", "denied", "authenticated", A,
     f"INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES ('{BOBS}', '{GOLD}', '{A}', 9)"),
    # item
    ("reviewer reads no rows of the item table itself", "count", "authenticated", A, "SELECT * FROM review.item", 0),
    ("reviewer sees only items assigned in open batches", "count", "authenticated", A, "SELECT * FROM review.item_reviewer", 2),
    ("reviewer sees no item of a closed batch", "count", "authenticated", A,
     f"SELECT * FROM review.item_reviewer WHERE batch_id = '{CLOSED}'", 0),
    ("reviewer sees no item of a draft batch", "count", "authenticated", A,
     f"SELECT * FROM review.item_reviewer WHERE batch_id = '{DRAFT}'", 0),
    ("reviewer sees no item assigned only to someone else", "count", "authenticated", A,
     "SELECT * FROM review.item_reviewer WHERE vocabulary = 'rvv'", 0),
    ("reviewer cannot read gold flag", "denied", "authenticated", A, "SELECT is_gold FROM review.item_reviewer"),
    ("reviewer cannot read gold answer", "denied", "authenticated", A, "SELECT gold_belongs FROM review.item_reviewer"),
    ("reviewer cannot read gold grade", "denied", "authenticated", A, "SELECT gold_grade FROM review.item_reviewer"),
    ("reviewer cannot read gold source", "denied", "authenticated", A, "SELECT gold_source FROM review.item_reviewer"),
    ("the reviewer item view has no gold column", "count", "postgres", None,
     "SELECT * FROM information_schema.columns WHERE table_schema = 'review' AND table_name = 'item_reviewer' AND column_name LIKE '%gold%'", 0),
    ("reviewer cannot insert an item", "denied", "authenticated", A,
     "INSERT INTO review.item (item_id, vocabulary, export_version, construct_pid, construct_label, construct_definition, measure_pid, programme, stratum) "
     "VALUES ('x', 'scv', 'x', 'x', 'x', 'x', 'x', 'x', '{}')"),
    # batch
    ("reviewer sees only batches they are assigned in", "count", "authenticated", A, "SELECT * FROM review.batch", 3),
    ("reviewer cannot see another reviewer's batch", "count", "authenticated", A, f"SELECT * FROM review.batch WHERE batch_id = '{BOBS}'", 0),
    ("reviewer cannot open a batch", "rows", "authenticated", A, f"UPDATE review.batch SET status = 'open' WHERE batch_id = '{DRAFT}'", 0),
    # response
    ("reviewer can answer their own assignment in an open batch", "allowed", "authenticated", A,
     f"INSERT INTO review.response (assignment_id, belongs) VALUES ({ALICE_OPEN}, 'yes')"),
    ("reviewer can record a curation answer with member answers", "allowed", "authenticated", A,
     f"INSERT INTO review.response (assignment_id, belongs, better_construct_pid, reject_reason, member_answers) "
     f"VALUES ({ALICE_OPEN}, 'neighbour', 'x:c/00002', NULL, '{{}}')"),
    ("reviewer cannot answer another reviewer's assignment", "denied", "authenticated", A,
     f"INSERT INTO review.response (assignment_id, belongs) VALUES ({BOB_ANY}, 'yes')"),
    ("reviewer cannot answer in a closed batch", "denied", "authenticated", A,
     f"INSERT INTO review.response (assignment_id, belongs) VALUES ({ALICE_CLOSED}, 'yes')"),
    ("reviewer cannot read another reviewer's responses", "count", "authenticated", A, "SELECT * FROM review.response", 0),
    ("reviewer cannot update a response", "denied", "authenticated", B, "UPDATE review.response SET belongs = 'no'"),
    ("reviewer cannot delete a response", "denied", "authenticated", B, "DELETE FROM review.response"),
    ("reviewer reads their own response", "count", "authenticated", B, "SELECT * FROM review.response", 1),
    # batch comment
    ("reviewer can comment on their own open batch", "allowed", "authenticated", A,
     f"INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES ('{OPEN}', '{A}', 'x')"),
    ("reviewer cannot comment on a closed batch", "denied", "authenticated", A,
     f"INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES ('{CLOSED}', '{A}', 'x')"),
    ("reviewer cannot comment as someone else", "denied", "authenticated", A,
     f"INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES ('{OPEN}', '{B}', 'x')"),
    ("reviewer cannot comment on another reviewer's batch", "denied", "authenticated", A,
     f"INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES ('{BOBS}', '{A}', 'x')"),
    ("reviewer cannot read another reviewer's comments", "count", "authenticated", A, "SELECT * FROM review.batch_comment", 0),
    ("reviewer cannot update a comment", "denied", "authenticated", B, "UPDATE review.batch_comment SET other = 'y'"),
    ("reviewer cannot delete a comment", "denied", "authenticated", B, "DELETE FROM review.batch_comment"),
    ("progress view shows only the reviewer's own batches", "count", "authenticated", A, "SELECT * FROM review.my_progress", 3),
    # inactive and unknown accounts
    ("inactive reviewer sees no items", "count", "authenticated", C, "SELECT * FROM review.item_reviewer", 0),
    ("inactive reviewer cannot answer", "denied", "authenticated", C,
     f"INSERT INTO review.response (assignment_id, belongs) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = '{C}'), 'yes')"),
    ("unknown signed in account sees no items", "count", "authenticated", X, "SELECT * FROM review.item_reviewer", 0),
    ("unknown signed in account sees no reviewer rows", "count", "authenticated", X, "SELECT * FROM review.reviewer", 0),
    ("signed in account without an email claim sees nothing", "count", "authenticated", "", "SELECT * FROM review.assignment", 0),
    # owner
    ("owner reads every item, gold included", "count", "authenticated", O, "SELECT * FROM review.item WHERE is_gold", 1),
    ("owner reads every item", "count", "authenticated", O, "SELECT * FROM review.item", 6),
    ("owner reads every assignment", "count", "authenticated", O, "SELECT * FROM review.assignment", 8),
    ("owner reads every response", "count", "authenticated", O, "SELECT * FROM review.response", 1),
    ("owner reads every reviewer", "count", "authenticated", O, "SELECT * FROM review.reviewer", 4),
    ("owner reads every batch", "count", "authenticated", O, "SELECT * FROM review.batch", 5),
    ("owner cannot insert an assignment from the browser", "denied", "authenticated", O,
     f"INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES ('{OPEN}', '{GOLD}', '{O}', 9)"),
    ("owner cannot update a response", "denied", "authenticated", O, "UPDATE review.response SET belongs = 'no'"),
    ("owner cannot delete a response", "denied", "authenticated", O, "DELETE FROM review.response"),
    # owner actions (migration 0002)
    ("owner can close a batch", "allowed", "authenticated", O, f"UPDATE review.batch SET status = 'closed' WHERE batch_id = '{OPEN}'"),
    ("reviewer cannot close a batch", "rows", "authenticated", A, f"UPDATE review.batch SET status = 'closed' WHERE batch_id = '{OPEN}'", 0),
    ("owner closes exactly the batch named", "rows", "authenticated", O, f"UPDATE review.batch SET status = 'closed' WHERE batch_id = '{OPEN}'", 1),
    ("owner cannot change a batch's sampling specification", "denied", "authenticated", O, "UPDATE review.batch SET sampling_spec = '{}'"),
    ("owner builds the next owner batch", "allowed", "authenticated", O, "SELECT review.owner_next_batch('test-0.0.1', 25, 0.5)"),
    ("owner builds the next curation batch", "allowed", "authenticated", O, "SELECT review.owner_next_queue_batch('test-0.0.1', 'placement', 5)"),
    ("reviewer cannot build an owner batch", "denied", "authenticated", A, "SELECT review.owner_next_batch('test-0.0.1', 25, 0.5)"),
    ("reviewer cannot build a curation batch", "denied", "authenticated", A, "SELECT review.owner_next_queue_batch('test-0.0.1', 'placement', 5)"),
    ("anon cannot build an owner batch", "denied", "anon", None, "SELECT review.owner_next_batch('test-0.0.1', 25, 0.5)"),
    # service key
    ("service key inserts an assignment", "allowed", "service_role", None,
     f"INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES ('{OPEN}', '{GOLD}', '{O}', 9)"),
    ("service key cannot update a response either", "denied", "service_role", None, "UPDATE review.response SET belongs = 'no'"),
    ("service key cannot delete a response either", "denied", "service_role", None, "DELETE FROM review.response"),
]


def q(s):
    return s.replace("'", "''")


def block(name, kind, role, email, stmt, expect=None):
    setup = "" if role == "postgres" else f"SET LOCAL ROLE {role}; "
    if email is not None:
        setup += f"PERFORM set_config('request.jwt.claims', '{q('{}' if email == '' else '{\"email\":\"' + email + '\"}')}', true); "
    n = q(name)
    if kind == "count":
        return (f"DO $$ DECLARE n bigint; BEGIN {setup}\n  SELECT count(*) INTO n FROM ({stmt}) t;\n  RESET ROLE;\n"
                f"  INSERT INTO rls_result VALUES ('{n}', n = {expect}, format('expected {expect}, got %s', n));\n"
                f"EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('{n}', false, SQLERRM); END $$;")
    if kind == "denied":
        return (f"DO $$ BEGIN {setup}\n  BEGIN\n    EXECUTE '{q(stmt)}';\n    RESET ROLE; INSERT INTO rls_result VALUES ('{n}', false, 'statement succeeded');\n"
                f"  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('{n}', true, SQLERRM); END;\nEND $$;")
    if kind == "rows":
        return (f"DO $$ DECLARE n bigint; BEGIN {setup}\n  BEGIN\n    EXECUTE '{q(stmt)}';\n    GET DIAGNOSTICS n = ROW_COUNT;\n"
                f"    RAISE EXCEPTION 'rows=%', n;\n  EXCEPTION WHEN others THEN RESET ROLE;\n"
                f"    INSERT INTO rls_result VALUES ('{n}', SQLERRM = 'rows={expect}', format('expected rows={expect}, got %s', SQLERRM)); END;\nEND $$;")
    return (f"DO $$ BEGIN {setup}\n  BEGIN\n    EXECUTE '{q(stmt)}';\n    RAISE EXCEPTION 'rollback_ok';\n"
            f"  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('{n}', SQLERRM = 'rollback_ok', SQLERRM); END;\nEND $$;")


out = ["-- Row level security tests (CLAUDE.md section 4). Written by tests/gen_rls.py, run by tests/run_rls.py.",
       "-- Every case runs against the fictional seed data in tests/seed.sql.", "",
       "DROP TABLE IF EXISTS rls_result;", "CREATE TABLE rls_result (name text, ok bool, detail text);", ""]
for c in CASES:
    out += [f"-- {c[0]}", block(*c), ""]
out += ["SELECT count(*) FILTER (WHERE ok) AS passed, count(*) FILTER (WHERE NOT ok) AS failed FROM rls_result;"]
Path(__file__).with_name("rls.sql").write_text("\n".join(out) + "\n")
print(len(CASES), "cases written to tests/rls.sql")

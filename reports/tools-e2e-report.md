# Tools end to end test report

Run 2026-10-30 21:30 UTC by `tests/run_tools_e2e.py` on fictional data in a throwaway Postgres 16 container with the Supabase roles emulated. Fictional vocabulary repositories in a temporary folder.

20 steps, 20 passed.

| Step | Result | Detail |
|---|---|---|
| reviewers added | pass | {"rows": 3, "auth_created": 0, "auth_existing": 0} |
| survey items loaded | pass | {"scv-test-0.0.1.jsonl": 80, "gold": 6, "items_in_db_for_export": 80} |
| register items and queues loaded | pass | {"rvv-test-0.0.1.jsonl": 80, "queue membership": 3, "queue placement": 12, "gold": 6, "items_in_db_for_export": 95} |
| a file with an invalid line is refused | pass | xreafj/bad/scv/review/items/scv-test-0.0.1.jsonl with 1 invalid lines, for example ["scv-test-0.0.1.jsonl:81 'export_version' is a required property"] |
| owner quality batch of 25 | pass | b-20261030-01 {"items": 25, "gold": 3, "overlap": 0, "status": "open"} |
| invited batch of 25 with 15 percent overlap | pass | b-20261030-02 {"items": 25, "gold": 3, "overlap": 3, "status": "open"} |
| invited batch outside 20 to 30 is refused | pass | batches for invited reviewers have 20 to 30 items (section 6, V-07 25) |
| owner curation batch, placement queue | pass | b-20261030-03 {"items": 10, "gold": 0, "overlap": 0, "status": "open"} |
| owner register quality batch | pass | b-20261030-04 {"items": 25, "gold": 3, "overlap": 0, "status": "open"} |
| owner batch built on request from the admin screen | pass | b-20261030-05, 25 items, 3 gold, 0 repeated from earlier batches. Curation batch b-20261030-06 |
| answers given through RLS | pass | {"owner@example.org": 88, "r1@example.org": 25, "r2@example.org": 3} |
| survey export with round trip check | pass | e2e {"items": 57, "batches": 3, "assignments": 78, "responses": 94, "current_responses": 78, "batch_comments": 4, "responses_in_db": 94} |
| register export with round trip check | pass | e2e {"items": 38, "batches": 3, "assignments": 38, "responses": 46, "current_responses": 38, "batch_comments": 3, "responses_in_db": 46} |
| every response row is in an export | pass | 140 in the database, 140 in the exports |
| no email in the export files except the key | pass |  |
| the key is gitignored | pass |  |
| survey analysis | pass | /private/var/folders/89/036wjl9s7d3_96q79bbxpvn80000gn/T/review-e2e-zgxreafj/scv/reports/review-2026-10-30.md {"responses": 78, "quality": 78, "Invited rounds a |
| register analysis | pass | /private/var/folders/89/036wjl9s7d3_96q79bbxpvn80000gn/T/review-e2e-zgxreafj/rvv/reports/review-2026-10-30.md {"responses": 38, "quality": 25, "Owner rounds ans |
| the joined export has every column apply_curation.py reads | pass | 13 curation answers |
| every tool run is an audit event in the vocabulary repository | pass | survey 5, register 5 |

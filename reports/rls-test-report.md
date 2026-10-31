# Row level security test report

Run 2026-10-31 18:30 UTC on Postgres 16.15 in a local container, with the Supabase roles and auth.jwt() emulated as Supabase implements them (`tests/supabase_shim.sql`). Data is the fictional seed (`tests/seed.sql`).

67 cases, 67 passed, 0 failed.

| Case | Result | Detail |
|---|---|---|
| anon cannot read reviewers | pass | permission denied for schema review |
| anon cannot read items | pass | permission denied for schema review |
| anon cannot read the reviewer item view | pass | permission denied for schema review |
| anon cannot read responses | pass | permission denied for schema review |
| anon cannot insert a response | pass | permission denied for schema review |
| reviewer sees only their own reviewer row | pass | expected 1, got 1 |
| reviewer cannot see another reviewer's row | pass | expected 0, got 0 |
| reviewer sees only their own assignments | pass | expected 4, got 4 |
| reviewer cannot read another reviewer's assignments | pass | expected 0, got 0 |
| reviewer cannot insert an assignment | pass | permission denied for table assignment |
| reviewer reads no rows of the item table itself | pass | expected 0, got 0 |
| reviewer sees only items assigned in open batches | pass | expected 2, got 2 |
| reviewer sees no item of a closed batch | pass | expected 0, got 0 |
| reviewer sees no item of a draft batch | pass | expected 0, got 0 |
| reviewer sees no item assigned only to someone else | pass | expected 0, got 0 |
| reviewer cannot read gold flag | pass | column "is_gold" does not exist |
| reviewer cannot read gold answer | pass | column "gold_belongs" does not exist |
| reviewer cannot read gold grade | pass | column "gold_grade" does not exist |
| reviewer cannot read gold source | pass | column "gold_source" does not exist |
| the reviewer item view has no gold column | pass | expected 0, got 0 |
| reviewer cannot insert an item | pass | permission denied for table item |
| reviewer sees only batches they are assigned in | pass | expected 3, got 3 |
| reviewer cannot see another reviewer's batch | pass | expected 0, got 0 |
| reviewer cannot open a batch | pass | expected rows=0, got rows=0 |
| reviewer can answer their own assignment in an open batch | pass | rollback_ok |
| reviewer can record a curation answer with member answers | pass | rollback_ok |
| reviewer cannot answer another reviewer's assignment | pass | new row violates row-level security policy for table "response" |
| reviewer cannot answer in a closed batch | pass | new row violates row-level security policy for table "response" |
| reviewer cannot read another reviewer's responses | pass | expected 0, got 0 |
| reviewer cannot update a response | pass | permission denied for table response |
| reviewer cannot delete a response | pass | permission denied for table response |
| reviewer reads their own response | pass | expected 1, got 1 |
| reviewer can comment on their own open batch | pass | rollback_ok |
| reviewer cannot comment on a closed batch | pass | new row violates row-level security policy for table "batch_comment" |
| reviewer cannot comment as someone else | pass | new row violates row-level security policy for table "batch_comment" |
| reviewer cannot comment on another reviewer's batch | pass | new row violates row-level security policy for table "batch_comment" |
| reviewer cannot read another reviewer's comments | pass | expected 0, got 0 |
| reviewer cannot update a comment | pass | permission denied for table batch_comment |
| reviewer cannot delete a comment | pass | permission denied for table batch_comment |
| progress view shows only the reviewer's own batches | pass | expected 3, got 3 |
| inactive reviewer sees no items | pass | expected 0, got 0 |
| inactive reviewer cannot answer | pass | new row violates row-level security policy for table "response" |
| unknown signed in account sees no items | pass | expected 0, got 0 |
| unknown signed in account sees no reviewer rows | pass | expected 0, got 0 |
| signed in account without an email claim sees nothing | pass | expected 0, got 0 |
| owner reads every item, gold included | pass | expected 1, got 1 |
| owner reads every item | pass | expected 6, got 6 |
| owner reads every assignment | pass | expected 8, got 8 |
| owner reads every response | pass | expected 1, got 1 |
| owner reads every reviewer | pass | expected 4, got 4 |
| owner reads every batch | pass | expected 5, got 5 |
| owner cannot insert an assignment from the browser | pass | permission denied for table assignment |
| owner cannot update a response | pass | permission denied for table response |
| owner cannot delete a response | pass | permission denied for table response |
| owner can close a batch | pass | rollback_ok |
| reviewer cannot close a batch | pass | expected rows=0, got rows=0 |
| owner closes exactly the batch named | pass | expected rows=1, got rows=1 |
| owner cannot change a batch's sampling specification | pass | permission denied for table batch |
| reviewer cannot mark a batch as a flow test | pass | permission denied for table batch |
| owner builds the next owner batch | pass | rollback_ok |
| owner builds the next curation batch | pass | rollback_ok |
| reviewer cannot build an owner batch | pass | owner only |
| reviewer cannot build a curation batch | pass | owner only |
| anon cannot build an owner batch | pass | permission denied for schema review |
| service key inserts an assignment | pass | rollback_ok |
| service key cannot update a response either | pass | review.response is append only |
| service key cannot delete a response either | pass | review.response is append only |

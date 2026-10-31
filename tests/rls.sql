-- Row level security tests (CLAUDE.md section 4). Written by tests/gen_rls.py, run by tests/run_rls.py.
-- Every case runs against the fictional seed data in tests/seed.sql.

DROP TABLE IF EXISTS rls_result;
CREATE TABLE rls_result (name text, ok bool, detail text);

-- anon cannot read reviewers
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'SELECT * FROM review.reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read reviewers', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read reviewers', true, SQLERRM); END;
END $$;

-- anon cannot read items
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'SELECT * FROM review.item';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read items', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read items', true, SQLERRM); END;
END $$;

-- anon cannot read the reviewer item view
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'SELECT * FROM review.item_reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read the reviewer item view', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read the reviewer item view', true, SQLERRM); END;
END $$;

-- anon cannot read responses
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'SELECT * FROM review.response';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read responses', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot read responses', true, SQLERRM); END;
END $$;

-- anon cannot insert a response
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs) VALUES (1, ''yes'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot insert a response', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot insert a response', true, SQLERRM); END;
END $$;

-- reviewer sees only their own reviewer row
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees only their own reviewer row', n = 1, format('expected 1, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees only their own reviewer row', false, SQLERRM); END $$;

-- reviewer cannot see another reviewer's row
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.reviewer WHERE email = 'bob@example.org') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer cannot see another reviewer''s row', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot see another reviewer''s row', false, SQLERRM); END $$;

-- reviewer sees only their own assignments
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.assignment) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees only their own assignments', n = 4, format('expected 4, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees only their own assignments', false, SQLERRM); END $$;

-- reviewer cannot read another reviewer's assignments
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.assignment WHERE reviewer_email <> 'alice@example.org') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s assignments', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s assignments', false, SQLERRM); END $$;

-- reviewer cannot insert an assignment
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES (''b-20261030-04'', ''scv:x:m/test/000001:x:c/00001:test-0.0.1'', ''alice@example.org'', 9)';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot insert an assignment', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot insert an assignment', true, SQLERRM); END;
END $$;

-- reviewer reads no rows of the item table itself
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer reads no rows of the item table itself', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer reads no rows of the item table itself', false, SQLERRM); END $$;

-- reviewer sees only items assigned in open batches
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees only items assigned in open batches', n = 2, format('expected 2, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees only items assigned in open batches', false, SQLERRM); END $$;

-- reviewer sees no item of a closed batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer WHERE batch_id = 'b-20261030-02') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees no item of a closed batch', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees no item of a closed batch', false, SQLERRM); END $$;

-- reviewer sees no item of a draft batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer WHERE batch_id = 'b-20261030-03') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees no item of a draft batch', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees no item of a draft batch', false, SQLERRM); END $$;

-- reviewer sees no item assigned only to someone else
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer WHERE vocabulary = 'rvv') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees no item assigned only to someone else', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees no item assigned only to someone else', false, SQLERRM); END $$;

-- reviewer cannot read gold flag
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT is_gold FROM review.item_reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold flag', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold flag', true, SQLERRM); END;
END $$;

-- reviewer cannot read gold answer
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT gold_belongs FROM review.item_reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold answer', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold answer', true, SQLERRM); END;
END $$;

-- reviewer cannot read gold grade
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT gold_grade FROM review.item_reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold grade', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold grade', true, SQLERRM); END;
END $$;

-- reviewer cannot read gold source
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT gold_source FROM review.item_reviewer';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold source', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read gold source', true, SQLERRM); END;
END $$;

-- the reviewer item view has no gold column
DO $$ DECLARE n bigint; BEGIN 
  SELECT count(*) INTO n FROM (SELECT * FROM information_schema.columns WHERE table_schema = 'review' AND table_name = 'item_reviewer' AND column_name LIKE '%gold%') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('the reviewer item view has no gold column', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('the reviewer item view has no gold column', false, SQLERRM); END $$;

-- reviewer cannot insert an item
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.item (item_id, vocabulary, export_version, construct_pid, construct_label, construct_definition, measure_pid, programme, stratum) VALUES (''x'', ''scv'', ''x'', ''x'', ''x'', ''x'', ''x'', ''x'', ''{}'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot insert an item', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot insert an item', true, SQLERRM); END;
END $$;

-- reviewer sees only batches they are assigned in
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.batch) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer sees only batches they are assigned in', n = 3, format('expected 3, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer sees only batches they are assigned in', false, SQLERRM); END $$;

-- reviewer cannot see another reviewer's batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.batch WHERE batch_id = 'b-20261030-04') t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer cannot see another reviewer''s batch', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot see another reviewer''s batch', false, SQLERRM); END $$;

-- reviewer cannot open a batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET status = ''open'' WHERE batch_id = ''b-20261030-03''';
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE EXCEPTION 'rows=%', n;
  EXCEPTION WHEN others THEN RESET ROLE;
    INSERT INTO rls_result VALUES ('reviewer cannot open a batch', SQLERRM = 'rows=0', format('expected rows=0, got %s', SQLERRM)); END;
END $$;

-- reviewer can answer their own assignment in an open batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = ''alice@example.org'' AND batch_id = ''b-20261030-01'' AND position = 1), ''yes'')';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer can answer their own assignment in an open batch', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- reviewer can record a curation answer with member answers
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs, better_construct_pid, reject_reason, member_answers) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = ''alice@example.org'' AND batch_id = ''b-20261030-01'' AND position = 1), ''neighbour'', ''x:c/00002'', NULL, ''{}'')';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer can record a curation answer with member answers', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- reviewer cannot answer another reviewer's assignment
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = ''bob@example.org'' AND batch_id = ''b-20261030-04'' AND position = 1), ''yes'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot answer another reviewer''s assignment', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot answer another reviewer''s assignment', true, SQLERRM); END;
END $$;

-- reviewer cannot answer in a closed batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = ''alice@example.org'' AND batch_id = ''b-20261030-02''), ''yes'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot answer in a closed batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot answer in a closed batch', true, SQLERRM); END;
END $$;

-- reviewer cannot read another reviewer's responses
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.response) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s responses', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s responses', false, SQLERRM); END $$;

-- reviewer cannot update a response
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"bob@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.response SET belongs = ''no''';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot update a response', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot update a response', true, SQLERRM); END;
END $$;

-- reviewer cannot delete a response
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"bob@example.org"}', true); 
  BEGIN
    EXECUTE 'DELETE FROM review.response';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot delete a response', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot delete a response', true, SQLERRM); END;
END $$;

-- reviewer reads their own response
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"bob@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.response) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer reads their own response', n = 1, format('expected 1, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer reads their own response', false, SQLERRM); END $$;

-- reviewer can comment on their own open batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES (''b-20261030-01'', ''alice@example.org'', ''x'')';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer can comment on their own open batch', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- reviewer cannot comment on a closed batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES (''b-20261030-02'', ''alice@example.org'', ''x'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment on a closed batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment on a closed batch', true, SQLERRM); END;
END $$;

-- reviewer cannot comment as someone else
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES (''b-20261030-01'', ''bob@example.org'', ''x'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment as someone else', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment as someone else', true, SQLERRM); END;
END $$;

-- reviewer cannot comment on another reviewer's batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES (''b-20261030-04'', ''alice@example.org'', ''x'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment on another reviewer''s batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot comment on another reviewer''s batch', true, SQLERRM); END;
END $$;

-- reviewer cannot read another reviewer's comments
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.batch_comment) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s comments', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot read another reviewer''s comments', false, SQLERRM); END $$;

-- reviewer cannot update a comment
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"bob@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch_comment SET other = ''y''';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot update a comment', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot update a comment', true, SQLERRM); END;
END $$;

-- reviewer cannot delete a comment
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"bob@example.org"}', true); 
  BEGIN
    EXECUTE 'DELETE FROM review.batch_comment';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot delete a comment', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot delete a comment', true, SQLERRM); END;
END $$;

-- progress view shows only the reviewer's own batches
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.my_progress) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('progress view shows only the reviewer''s own batches', n = 3, format('expected 3, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('progress view shows only the reviewer''s own batches', false, SQLERRM); END $$;

-- inactive reviewer sees no items
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"carol@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('inactive reviewer sees no items', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('inactive reviewer sees no items', false, SQLERRM); END $$;

-- inactive reviewer cannot answer
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"carol@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.response (assignment_id, belongs) VALUES ((SELECT assignment_id FROM review.assignment WHERE reviewer_email = ''carol@example.org''), ''yes'')';
    RESET ROLE; INSERT INTO rls_result VALUES ('inactive reviewer cannot answer', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('inactive reviewer cannot answer', true, SQLERRM); END;
END $$;

-- unknown signed in account sees no items
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"nobody@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item_reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('unknown signed in account sees no items', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('unknown signed in account sees no items', false, SQLERRM); END $$;

-- unknown signed in account sees no reviewer rows
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"nobody@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('unknown signed in account sees no reviewer rows', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('unknown signed in account sees no reviewer rows', false, SQLERRM); END $$;

-- signed in account without an email claim sees nothing
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.assignment) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('signed in account without an email claim sees nothing', n = 0, format('expected 0, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('signed in account without an email claim sees nothing', false, SQLERRM); END $$;

-- owner reads every item, gold included
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item WHERE is_gold) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every item, gold included', n = 1, format('expected 1, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every item, gold included', false, SQLERRM); END $$;

-- owner reads every item
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.item) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every item', n = 6, format('expected 6, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every item', false, SQLERRM); END $$;

-- owner reads every assignment
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.assignment) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every assignment', n = 8, format('expected 8, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every assignment', false, SQLERRM); END $$;

-- owner reads every response
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.response) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every response', n = 1, format('expected 1, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every response', false, SQLERRM); END $$;

-- owner reads every reviewer
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.reviewer) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every reviewer', n = 4, format('expected 4, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every reviewer', false, SQLERRM); END $$;

-- owner reads every batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  SELECT count(*) INTO n FROM (SELECT * FROM review.batch) t;
  RESET ROLE;
  INSERT INTO rls_result VALUES ('owner reads every batch', n = 5, format('expected 5, got %s', n));
EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner reads every batch', false, SQLERRM); END $$;

-- owner cannot insert an assignment from the browser
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES (''b-20261030-01'', ''scv:x:m/test/000001:x:c/00001:test-0.0.1'', ''owner@example.org'', 9)';
    RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot insert an assignment from the browser', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot insert an assignment from the browser', true, SQLERRM); END;
END $$;

-- owner cannot update a response
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.response SET belongs = ''no''';
    RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot update a response', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot update a response', true, SQLERRM); END;
END $$;

-- owner cannot delete a response
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'DELETE FROM review.response';
    RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot delete a response', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot delete a response', true, SQLERRM); END;
END $$;

-- owner can close a batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET status = ''closed'' WHERE batch_id = ''b-20261030-01''';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner can close a batch', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- reviewer cannot close a batch
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET status = ''closed'' WHERE batch_id = ''b-20261030-01''';
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE EXCEPTION 'rows=%', n;
  EXCEPTION WHEN others THEN RESET ROLE;
    INSERT INTO rls_result VALUES ('reviewer cannot close a batch', SQLERRM = 'rows=0', format('expected rows=0, got %s', SQLERRM)); END;
END $$;

-- owner closes exactly the batch named
DO $$ DECLARE n bigint; BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET status = ''closed'' WHERE batch_id = ''b-20261030-01''';
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE EXCEPTION 'rows=%', n;
  EXCEPTION WHEN others THEN RESET ROLE;
    INSERT INTO rls_result VALUES ('owner closes exactly the batch named', SQLERRM = 'rows=1', format('expected rows=1, got %s', SQLERRM)); END;
END $$;

-- owner cannot change a batch's sampling specification
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET sampling_spec = ''{}''';
    RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot change a batch''s sampling specification', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner cannot change a batch''s sampling specification', true, SQLERRM); END;
END $$;

-- reviewer cannot mark a batch as a flow test
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'UPDATE review.batch SET flow_test = true WHERE batch_id = ''b-20261030-01''';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot mark a batch as a flow test', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot mark a batch as a flow test', true, SQLERRM); END;
END $$;

-- owner builds the next owner batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT review.owner_next_batch(''test-0.0.1'', 25, 0.5)';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner builds the next owner batch', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- owner builds the next curation batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"owner@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT review.owner_next_queue_batch(''test-0.0.1'', ''placement'', 5)';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('owner builds the next curation batch', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- reviewer cannot build an owner batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT review.owner_next_batch(''test-0.0.1'', 25, 0.5)';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot build an owner batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot build an owner batch', true, SQLERRM); END;
END $$;

-- reviewer cannot build a curation batch
DO $$ BEGIN SET LOCAL ROLE authenticated; PERFORM set_config('request.jwt.claims', '{"email":"alice@example.org"}', true); 
  BEGIN
    EXECUTE 'SELECT review.owner_next_queue_batch(''test-0.0.1'', ''placement'', 5)';
    RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot build a curation batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('reviewer cannot build a curation batch', true, SQLERRM); END;
END $$;

-- anon cannot build an owner batch
DO $$ BEGIN SET LOCAL ROLE anon; 
  BEGIN
    EXECUTE 'SELECT review.owner_next_batch(''test-0.0.1'', 25, 0.5)';
    RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot build an owner batch', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('anon cannot build an owner batch', true, SQLERRM); END;
END $$;

-- service key inserts an assignment
DO $$ BEGIN SET LOCAL ROLE service_role; 
  BEGIN
    EXECUTE 'INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position) VALUES (''b-20261030-01'', ''scv:x:m/test/000001:x:c/00001:test-0.0.1'', ''owner@example.org'', 9)';
    RAISE EXCEPTION 'rollback_ok';
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('service key inserts an assignment', SQLERRM = 'rollback_ok', SQLERRM); END;
END $$;

-- service key cannot update a response either
DO $$ BEGIN SET LOCAL ROLE service_role; 
  BEGIN
    EXECUTE 'UPDATE review.response SET belongs = ''no''';
    RESET ROLE; INSERT INTO rls_result VALUES ('service key cannot update a response either', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('service key cannot update a response either', true, SQLERRM); END;
END $$;

-- service key cannot delete a response either
DO $$ BEGIN SET LOCAL ROLE service_role; 
  BEGIN
    EXECUTE 'DELETE FROM review.response';
    RESET ROLE; INSERT INTO rls_result VALUES ('service key cannot delete a response either', false, 'statement succeeded');
  EXCEPTION WHEN others THEN RESET ROLE; INSERT INTO rls_result VALUES ('service key cannot delete a response either', true, SQLERRM); END;
END $$;

SELECT count(*) FILTER (WHERE ok) AS passed, count(*) FILTER (WHERE NOT ok) AS failed FROM rls_result;

-- Vocabulary review site, schema review (CLAUDE.md section 4, amendment 1 sections 12.3, 12.4 and 12.7).
-- Row level security is enabled on every table before any data is loaded (section 11). Reviewers read items only
-- through review.item_reviewer, which omits the gold fields. Responses and batch comments are append only.

CREATE SCHEMA IF NOT EXISTS review;
REVOKE ALL ON SCHEMA review FROM PUBLIC;
GRANT USAGE ON SCHEMA review TO authenticated, service_role;

CREATE TABLE review.reviewer (
  email text PRIMARY KEY CHECK (email = lower(email)),
  name text NOT NULL,
  affiliation text,
  expertise text[] DEFAULT '{}',          -- area tags, for example health, labour, family
  programmes text[] DEFAULT '{}',         -- programme or country codes they know, for example ess, liss, dk
  role text NOT NULL DEFAULT 'reviewer' CHECK (role IN ('reviewer', 'owner')),
  pseudonym text UNIQUE,                  -- r00 for the owner, r01 onward, used in exports (sections 7 and 12.4)
  consent_acknowledgement bool NOT NULL DEFAULT false,
  active bool NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE review.item (
  item_id text PRIMARY KEY,               -- <vocabulary>:<measure_pid>:<construct_pid>:<export_version>[:<queue>]
  vocabulary text NOT NULL CHECK (vocabulary IN ('scv', 'rvv')),
  export_version text NOT NULL,
  queue text CHECK (queue IN ('placement', 'membership')),   -- null for quality sample items (section 12.7)
  construct_pid text NOT NULL,
  construct_label text NOT NULL,
  construct_definition text NOT NULL,
  construct_exclusions text,
  construct_definition_provenance text,   -- person_written, draft_accepted, draft_generated and similar
  measure_pid text NOT NULL,              -- the represented variable PID for register items
  programme text NOT NULL,                -- or country and body for registers
  waves text,
  question_text text,                     -- or definition text for registers
  question_text_en text,
  text_kind text,
  response_categories jsonb,
  universe_text text,
  anchor_measure_pid text,
  anchor_question_text text,
  anchor_response_categories jsonb,
  grade text CHECK (grade IN ('identical', 'equivalent', 'related', 'distinct')),
  grade_reasons jsonb,
  method text,                            -- poc_full, poc_lowcost, poc_lowcost_v2, poc_register, not_graded, production
  model_confidence real,
  neighbour_constructs jsonb NOT NULL DEFAULT '[]',
  stratum jsonb NOT NULL,
  context jsonb NOT NULL DEFAULT '{}',    -- named card fields, shown in order (section 12.3)
  curation jsonb,                         -- queue items only, for example members, named members, note, reject reasons
  is_gold bool NOT NULL DEFAULT false,
  gold_belongs text CHECK (gold_belongs IN ('yes', 'no', 'unsure')),
  gold_grade text CHECK (gold_grade IN ('identical', 'equivalent', 'related', 'distinct')),
  gold_source text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE review.batch (
  batch_id text PRIMARY KEY,              -- b-<yyyymmdd>-<nn>
  vocabulary text NOT NULL CHECK (vocabulary IN ('scv', 'rvv')),
  kind text NOT NULL DEFAULT 'quality' CHECK (kind IN ('quality', 'curation')),
  description text,
  sampling_spec jsonb NOT NULL,           -- strata, sizes, seed, overlap share, gold count, or the queue and its range
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'closed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  closes_at timestamptz
);

CREATE TABLE review.assignment (
  assignment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id text NOT NULL REFERENCES review.batch,
  item_id text NOT NULL REFERENCES review.item,
  reviewer_email text NOT NULL REFERENCES review.reviewer,
  position int NOT NULL,
  is_overlap bool NOT NULL DEFAULT false,
  UNIQUE (batch_id, item_id, reviewer_email)
);

CREATE TABLE review.response (                -- append only, the latest row per assignment is current
  response_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assignment_id bigint NOT NULL REFERENCES review.assignment,
  belongs text CHECK (belongs IN ('yes', 'no', 'unsure', 'neighbour', 'reject')),   -- neighbour and reject on curation items
  better_construct_pid text,
  better_construct_text text,
  reject_reason text,
  member_answers jsonb,                   -- membership items, {member pid: {answer: stay|move|reject, target, reason}}
  grade_ok text CHECK (grade_ok IN ('yes', 'no', 'unsure', 'not_shown')),
  correct_grade text CHECK (correct_grade IN ('identical', 'equivalent', 'related', 'distinct')),
  comment text,
  seconds_on_item int,
  client_version text,
  submitted_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE review.batch_comment (
  comment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id text NOT NULL REFERENCES review.batch,
  reviewer_email text NOT NULL REFERENCES review.reviewer,
  missing_constructs text,
  systematic_issues text,
  other text,
  submitted_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON review.assignment (reviewer_email, batch_id);
CREATE INDEX ON review.assignment (item_id);
CREATE INDEX ON review.response (assignment_id, submitted_at);

-- Who is asking. The email claim of the Supabase JWT, lower case.
CREATE FUNCTION review.current_email() RETURNS text LANGUAGE sql STABLE AS
$$ SELECT lower(coalesce(auth.jwt() ->> 'email', '')) $$;

-- Security definer so the policies can read the reviewer table without recursing through its own policy.
CREATE FUNCTION review.is_owner() RETURNS bool LANGUAGE sql STABLE SECURITY DEFINER SET search_path = review, pg_temp AS
$$ SELECT EXISTS (SELECT 1 FROM review.reviewer WHERE email = review.current_email() AND role = 'owner' AND active) $$;

CREATE FUNCTION review.is_active_reviewer() RETURNS bool LANGUAGE sql STABLE SECURITY DEFINER SET search_path = review, pg_temp AS
$$ SELECT EXISTS (SELECT 1 FROM review.reviewer WHERE email = review.current_email() AND active) $$;

-- The assignment belongs to the caller and its batch is open.
CREATE FUNCTION review.own_open_assignment(a bigint) RETURNS bool LANGUAGE sql STABLE SECURITY DEFINER SET search_path = review, pg_temp AS
$$ SELECT EXISTS (SELECT 1 FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
                  WHERE s.assignment_id = a AND s.reviewer_email = review.current_email() AND b.status = 'open')
          AND review.is_active_reviewer() $$;

CREATE FUNCTION review.own_open_batch(bid text) RETURNS bool LANGUAGE sql STABLE SECURITY DEFINER SET search_path = review, pg_temp AS
$$ SELECT EXISTS (SELECT 1 FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
                  WHERE s.batch_id = bid AND s.reviewer_email = review.current_email() AND b.status = 'open')
          AND review.is_active_reviewer() $$;

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA review FROM PUBLIC;
GRANT EXECUTE ON FUNCTION review.current_email(), review.is_owner(), review.is_active_reviewer(),
  review.own_open_assignment(bigint), review.own_open_batch(text) TO authenticated;

ALTER TABLE review.reviewer ENABLE ROW LEVEL SECURITY;
ALTER TABLE review.item ENABLE ROW LEVEL SECURITY;
ALTER TABLE review.batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE review.assignment ENABLE ROW LEVEL SECURITY;
ALTER TABLE review.response ENABLE ROW LEVEL SECURITY;
ALTER TABLE review.batch_comment ENABLE ROW LEVEL SECURITY;

-- Grants. anon gets nothing. authenticated may read, and insert responses and comments. Only the service key writes the rest.
REVOKE ALL ON ALL TABLES IN SCHEMA review FROM PUBLIC, anon, authenticated;
GRANT SELECT ON review.reviewer, review.item, review.batch, review.assignment, review.response, review.batch_comment TO authenticated;
GRANT INSERT ON review.response, review.batch_comment TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA review TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA review TO authenticated, service_role;

-- reviewer. Own row, the owner all.
CREATE POLICY reviewer_select ON review.reviewer FOR SELECT TO authenticated
  USING (email = review.current_email() OR review.is_owner());

-- item. The table itself is for the owner only. Reviewers read review.item_reviewer.
CREATE POLICY item_owner ON review.item FOR SELECT TO authenticated USING (review.is_owner());

-- batch. Batches the reviewer has an assignment in, the owner all.
CREATE POLICY batch_select ON review.batch FOR SELECT TO authenticated
  USING (review.is_owner() OR EXISTS (SELECT 1 FROM review.assignment s WHERE s.batch_id = batch.batch_id
                                      AND s.reviewer_email = review.current_email()) AND review.is_active_reviewer());

-- assignment. Own rows, the owner all. Inserts only through the service key.
CREATE POLICY assignment_select ON review.assignment FOR SELECT TO authenticated
  USING ((reviewer_email = review.current_email() AND review.is_active_reviewer()) OR review.is_owner());

-- response. Insert only for own assignments in open batches, select own rows, the owner all. No update or delete.
CREATE POLICY response_insert ON review.response FOR INSERT TO authenticated
  WITH CHECK (review.own_open_assignment(assignment_id));
CREATE POLICY response_select ON review.response FOR SELECT TO authenticated
  USING (review.is_owner() OR EXISTS (SELECT 1 FROM review.assignment s WHERE s.assignment_id = response.assignment_id
                                      AND s.reviewer_email = review.current_email()));

-- batch_comment. As response.
CREATE POLICY comment_insert ON review.batch_comment FOR INSERT TO authenticated
  WITH CHECK (reviewer_email = review.current_email() AND review.own_open_batch(batch_id));
CREATE POLICY comment_select ON review.batch_comment FOR SELECT TO authenticated
  USING (reviewer_email = review.current_email() OR review.is_owner());

-- Append only. Updates and deletes of responses and comments are refused for every role but the database owner,
-- who removes a reviewer's data by hand on request (section 9).
CREATE FUNCTION review.refuse_change() RETURNS trigger LANGUAGE plpgsql AS
$$ BEGIN
  IF current_user NOT IN ('postgres', 'supabase_admin') THEN
    RAISE EXCEPTION 'review.% is append only', TG_TABLE_NAME;
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$;
CREATE TRIGGER response_append_only BEFORE UPDATE OR DELETE ON review.response FOR EACH ROW EXECUTE FUNCTION review.refuse_change();
CREATE TRIGGER comment_append_only BEFORE UPDATE OR DELETE ON review.batch_comment FOR EACH ROW EXECUTE FUNCTION review.refuse_change();

-- The reviewer's view of items. Gold fields are left out. Rows only for items the caller is assigned in an open
-- batch, with the assignment and position, so the front end needs no other read to show a batch.
-- The view runs with its owner's rights (security_invoker off), which is what lets it read review.item past the owner
-- only policy. RLS is not forced, so the table owner that owns the view reads the table, on Supabase as locally.
CREATE VIEW review.item_reviewer WITH (security_barrier = true) AS
SELECT s.assignment_id, s.batch_id, s.position, s.is_overlap, b.kind AS batch_kind,
       i.item_id, i.vocabulary, i.export_version, i.queue, i.construct_pid, i.construct_label, i.construct_definition,
       i.construct_exclusions, i.construct_definition_provenance, i.measure_pid, i.programme, i.waves, i.question_text,
       i.question_text_en, i.text_kind, i.response_categories, i.universe_text, i.anchor_measure_pid, i.anchor_question_text,
       i.anchor_response_categories, i.grade, i.grade_reasons, i.method, i.neighbour_constructs, i.context, i.curation
FROM review.assignment s
JOIN review.batch b ON b.batch_id = s.batch_id
JOIN review.item i ON i.item_id = s.item_id
WHERE s.reviewer_email = review.current_email() AND b.status = 'open' AND review.is_active_reviewer();
REVOKE ALL ON review.item_reviewer FROM PUBLIC, anon;
GRANT SELECT ON review.item_reviewer TO authenticated;

-- The current answer per assignment, for progress on the home screen and for resuming.
CREATE VIEW review.my_progress WITH (security_invoker = true) AS
SELECT s.batch_id, count(*) AS items, count(r.assignment_id) AS answered
FROM review.assignment s
LEFT JOIN (SELECT DISTINCT assignment_id FROM review.response) r ON r.assignment_id = s.assignment_id
WHERE s.reviewer_email = review.current_email()
GROUP BY s.batch_id;
REVOKE ALL ON review.my_progress FROM PUBLIC, anon;
GRANT SELECT ON review.my_progress TO authenticated;

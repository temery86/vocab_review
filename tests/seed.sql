-- Fictional seed data for the RLS tests and for trying the front end (section 11, seed data is fictional).
-- Nothing here comes from a vocabulary. Emails use the reserved example.org domain.

INSERT INTO review.reviewer (email, name, affiliation, expertise, programmes, role, pseudonym, consent_acknowledgement, active) VALUES
  ('owner@example.org', 'Test Owner', 'Example', '{family}', '{ess,dk}', 'owner', 'r00', true, true),
  ('alice@example.org', 'Alice Example', 'Example University', '{labour}', '{ess,liss}', 'reviewer', 'r01', true, true),
  ('bob@example.org', 'Bob Example', 'Example Institute', '{health}', '{dk,se}', 'reviewer', 'r02', false, true),
  ('carol@example.org', 'Carol Example', 'Example College', '{}', '{}', 'reviewer', 'r03', false, false);

INSERT INTO review.item (item_id, vocabulary, export_version, queue, construct_pid, construct_label, construct_definition,
  construct_exclusions, construct_definition_provenance, measure_pid, programme, waves, question_text, question_text_en, text_kind,
  response_categories, universe_text, anchor_measure_pid, anchor_question_text, anchor_response_categories, grade, grade_reasons, method,
  model_confidence, neighbour_constructs, stratum, context, curation, is_gold, gold_belongs, gold_grade, gold_source) VALUES
  ('scv:x:m/test/000001:x:c/00001:test-0.0.1', 'scv', 'test-0.0.1', NULL, 'x:c/00001', 'Fictional trust in neighbours',
   'How far a person trusts the people living near them.', 'Excludes trust in institutions.', 'person_written',
   'x:m/test/000001', 'test', 'w1 to w3 (2001 to 2005), 3 waves', 'How much do you trust your neighbours?', NULL, 'question',
   '[{"code":"1","label":"Not at all"},{"code":"2","label":"A little"},{"code":"3","label":"A lot"}]', 'All respondents',
   'x:m/test/000002', 'Do you trust the people in your street?', '[{"code":"1","label":"No"},{"code":"2","label":"Yes"}]',
   'related', '{"differs":["response_format"]}', 'poc_full', 0.9,
   '[{"pid":"x:c/00002","label":"Fictional trust in strangers"},{"pid":"x:c/00003","label":"Fictional neighbourhood safety"}]',
   '{"programme":"test","method":"poc_full"}', '{"label":"trust neighbours"}', NULL, true, 'yes', 'related', 'fictional gold'),
  ('scv:x:m/test/000003:x:c/00001:test-0.0.1', 'scv', 'test-0.0.1', NULL, 'x:c/00001', 'Fictional trust in neighbours',
   'How far a person trusts the people living near them.', NULL, 'draft_accepted', 'x:m/test/000003', 'test', 'w2', 'Fictional question three', NULL,
   'question', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'not_graded', 0.8, '[]', '{"programme":"test"}', '{}', NULL, false, NULL, NULL, NULL),
  ('scv:x:m/test/000004:x:c/00001:test-0.0.1', 'scv', 'test-0.0.1', NULL, 'x:c/00001', 'Fictional trust in neighbours',
   'How far a person trusts the people living near them.', NULL, 'draft_accepted', 'x:m/test/000004', 'test', 'w3', 'Fictional question four', NULL,
   'question', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'not_graded', 0.8, '[]', '{"programme":"test"}', '{}', NULL, false, NULL, NULL, NULL),
  ('scv:x:m/test/000005:x:c/00001:test-0.0.1', 'scv', 'test-0.0.1', NULL, 'x:c/00001', 'Fictional trust in neighbours',
   'How far a person trusts the people living near them.', NULL, 'draft_accepted', 'x:m/test/000005', 'test', 'w3', 'Fictional question five', NULL,
   'question', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'not_graded', 0.8, '[]', '{"programme":"test"}', '{}', NULL, false, NULL, NULL, NULL),
  ('rvv:x:r/xx/test/000001:x:c/00101:test-0.0.1:placement', 'rvv', 'test-0.0.1', 'placement', 'x:c/00101', 'Fictional year of moving',
   'The calendar year in which a person last moved home.', NULL, 'draft_generated', 'x:r/xx/test/000001', 'xx/test', '2001 to 2010',
   'Jahr des Umzugs', 'Year of the move', 'definition', NULL, 'Residents', NULL, NULL, NULL, NULL, NULL, 'not_graded', NULL,
   '[{"pid":"x:c/00102","label":"Fictional date of moving"}]', '{"country":"xx","placement":"R-29 join"}',
   '{"variable_name":"UMZ_JAHR","label":"Jahr des Umzugs","label_en":"Year of the move","definition_kind":"office"}',
   '{"reject_reasons":["technical","identifier","other"]}', false, NULL, NULL, NULL),
  ('rvv:membership/M001:x:c/00101:test-0.0.1', 'rvv', 'test-0.0.1', 'membership', 'x:c/00101', 'Fictional year of moving',
   'The calendar year in which a person last moved home.', NULL, 'draft_generated', 'membership/M001', 'xx/test', NULL, NULL, NULL, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'not_graded', NULL, '[]', '{"queue":"membership"}', '{}',
   '{"note":"Fictional note","members":[{"pid":"x:r/xx/test/000001","label":"Jahr des Umzugs"}],"named_members":["x:r/xx/test/000001"],"answers_per_member":["stay","move","reject"]}',
   false, NULL, NULL, NULL);

INSERT INTO review.batch (batch_id, vocabulary, kind, description, sampling_spec, status) VALUES
  ('b-20261030-01', 'scv', 'quality', 'Fictional open batch for Alice', '{"seed":1,"size":3}', 'open'),
  ('b-20261030-02', 'scv', 'quality', 'Fictional closed batch for Alice', '{"seed":2,"size":1}', 'closed'),
  ('b-20261030-03', 'scv', 'quality', 'Fictional draft batch for Alice', '{"seed":3,"size":1}', 'draft'),
  ('b-20261030-04', 'rvv', 'curation', 'Fictional open curation batch for Bob', '{"queue":"placement"}', 'open'),
  ('b-20261030-05', 'scv', 'quality', 'Fictional open batch for Carol, who is inactive', '{"seed":5}', 'open');

INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap) VALUES
  ('b-20261030-01', 'scv:x:m/test/000001:x:c/00001:test-0.0.1', 'alice@example.org', 1, false),
  ('b-20261030-01', 'scv:x:m/test/000003:x:c/00001:test-0.0.1', 'alice@example.org', 2, false),
  ('b-20261030-02', 'scv:x:m/test/000004:x:c/00001:test-0.0.1', 'alice@example.org', 1, false),
  ('b-20261030-03', 'scv:x:m/test/000005:x:c/00001:test-0.0.1', 'alice@example.org', 1, false),
  ('b-20261030-04', 'rvv:x:r/xx/test/000001:x:c/00101:test-0.0.1:placement', 'bob@example.org', 1, false),
  ('b-20261030-04', 'rvv:membership/M001:x:c/00101:test-0.0.1', 'bob@example.org', 2, false),
  ('b-20261030-01', 'scv:x:m/test/000001:x:c/00001:test-0.0.1', 'bob@example.org', 1, true),
  ('b-20261030-05', 'scv:x:m/test/000003:x:c/00001:test-0.0.1', 'carol@example.org', 1, false);

-- One answer by Bob, inserted as the service key would, so Alice can be tested against it.
INSERT INTO review.response (assignment_id, belongs, comment)
  SELECT assignment_id, 'yes', 'Fictional answer by Bob' FROM review.assignment WHERE reviewer_email = 'bob@example.org' AND position = 1 AND batch_id = 'b-20261030-04';
INSERT INTO review.batch_comment (batch_id, reviewer_email, other) VALUES ('b-20261030-04', 'bob@example.org', 'Fictional comment by Bob');

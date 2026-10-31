-- Batches marked as a flow test (Tom Emery, 31 October 2026). Answers in them are kept, as every answer is, but analysis
-- leaves them out, and their items can be drawn again for the same reviewer.

ALTER TABLE review.batch ADD COLUMN IF NOT EXISTS flow_test bool NOT NULL DEFAULT false;

-- owner_next_batch, as in 0002, with assignments in flow test batches not counted as seen or covered.
CREATE OR REPLACE FUNCTION review.owner_next_batch(p_export text, p_size int, p_seed double precision DEFAULT random())
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path = review, pg_temp AS $$
DECLARE
  v_email text := review.current_email();
  v_vocab text;
  v_keys text[];
  v_gold int := round(p_size * 3.0 / 25);
  v_id text;
BEGIN
  IF NOT review.is_owner() THEN RAISE EXCEPTION 'owner only'; END IF;
  IF p_size < 25 OR p_size > 100 THEN RAISE EXCEPTION 'owner batches have 25 to 100 items (V-07)'; END IF;
  SELECT vocabulary INTO v_vocab FROM review.item WHERE export_version = p_export LIMIT 1;
  IF v_vocab IS NULL THEN RAISE EXCEPTION 'no items of %', p_export; END IF;
  v_keys := CASE v_vocab WHEN 'scv' THEN ARRAY['programme', 'construct_type', 'method', 'grade']
                         ELSE ARRAY['country', 'placement', 'statement_basis', 'poc_member'] END;
  PERFORM setseed(p_seed);
  SELECT 'b-' || to_char(now(), 'YYYYMMDD') || '-' || lpad((count(*) + 1)::text, 2, '0') INTO v_id
    FROM review.batch WHERE batch_id LIKE 'b-' || to_char(now(), 'YYYYMMDD') || '-%';
  INSERT INTO review.batch (batch_id, vocabulary, kind, description, sampling_spec, status)
  VALUES (v_id, v_vocab, 'quality', format('owner batch of %s from %s, built on request', p_size, p_export),
          jsonb_build_object('kind', 'quality', 'export', p_export, 'size', p_size, 'seed', p_seed, 'cells', v_keys, 'gold', v_gold,
                             'overlap_share', 0, 'owner_round', true, 'built_by', 'review.owner_next_batch'), 'open');
  WITH mine AS (
    SELECT s.item_id FROM review.assignment s JOIN review.batch b ON b.batch_id = s.batch_id
    WHERE s.reviewer_email = v_email AND NOT b.flow_test AND s.batch_id <> v_id),
  covered AS (
    SELECT DISTINCT (SELECT array_agg(i.stratum ->> k) FROM unnest(v_keys) k) AS cell FROM mine m JOIN review.item i ON i.item_id = m.item_id),
  blocked AS (
    SELECT i.measure_pid, i.construct_pid FROM review.item i JOIN review.assignment s ON s.item_id = i.item_id
    JOIN review.batch b ON b.batch_id = s.batch_id WHERE i.queue IS NOT NULL AND b.status IN ('open', 'draft')),
  pool AS (
    SELECT i.item_id, i.is_gold, (SELECT array_agg(i.stratum ->> k) FROM unnest(v_keys) k) AS cell, random() AS r
    FROM review.item i
    WHERE i.export_version = p_export AND i.queue IS NULL
      AND NOT EXISTS (SELECT 1 FROM mine m WHERE m.item_id = i.item_id)
      AND NOT EXISTS (SELECT 1 FROM blocked x WHERE x.measure_pid = i.measure_pid AND x.construct_pid = i.construct_pid)),
  ranked AS (
    SELECT item_id, is_gold, row_number() OVER (PARTITION BY cell ORDER BY r) AS k, cell IN (SELECT cell FROM covered) AS old, r FROM pool),
  main AS (SELECT item_id FROM ranked WHERE NOT is_gold ORDER BY old, k, r LIMIT p_size - v_gold),
  gold AS (SELECT item_id FROM ranked WHERE is_gold ORDER BY r LIMIT v_gold),
  chosen AS (SELECT item_id, row_number() OVER (ORDER BY random()) AS pos FROM (SELECT item_id FROM main UNION ALL SELECT item_id FROM gold) u)
  INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap)
  SELECT v_id, item_id, v_email, pos, false FROM chosen;
  RETURN v_id;
END $$;
REVOKE ALL ON FUNCTION review.owner_next_batch(text, int, double precision) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION review.owner_next_batch(text, int, double precision) TO authenticated;

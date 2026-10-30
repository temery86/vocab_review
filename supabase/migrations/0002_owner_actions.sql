-- Owner actions from the admin screen (sections 5 screen 6 and 12.4). The owner opens and closes batches and builds the
-- next owner batch on request. Both are refused for everyone else. Invited rounds are still built offline by
-- tools/make_batch.py, which also writes the specification into the vocabulary repository.

GRANT UPDATE (status, closes_at) ON review.batch TO authenticated;
CREATE POLICY batch_owner_update ON review.batch FOR UPDATE TO authenticated USING (review.is_owner()) WITH CHECK (review.is_owner());

-- The next owner batch of a quality sample (12.4). Cells are the vocabulary's stratum keys, cells the owner has not
-- yet been given come first, items the owner already has are never drawn again, and gold items are added at 3 per
-- 25 (V-07). The seed is recorded so the batch can be rebuilt.
CREATE FUNCTION review.owner_next_batch(p_export text, p_size int, p_seed double precision DEFAULT random())
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
  WITH covered AS (
    SELECT DISTINCT (SELECT array_agg(i.stratum ->> k) FROM unnest(v_keys) k) AS cell
    FROM review.assignment s JOIN review.item i ON i.item_id = s.item_id WHERE s.reviewer_email = v_email),
  blocked AS (
    SELECT i.measure_pid, i.construct_pid FROM review.item i JOIN review.assignment s ON s.item_id = i.item_id
    JOIN review.batch b ON b.batch_id = s.batch_id WHERE i.queue IS NOT NULL AND b.status IN ('open', 'draft')),
  pool AS (
    SELECT i.item_id, i.is_gold, (SELECT array_agg(i.stratum ->> k) FROM unnest(v_keys) k) AS cell, random() AS r
    FROM review.item i
    WHERE i.export_version = p_export AND i.queue IS NULL
      AND NOT EXISTS (SELECT 1 FROM review.assignment s WHERE s.item_id = i.item_id AND s.reviewer_email = v_email)
      AND NOT EXISTS (SELECT 1 FROM blocked x WHERE x.measure_pid = i.measure_pid AND x.construct_pid = i.construct_pid)),
  ranked AS (
    SELECT item_id, is_gold, row_number() OVER (PARTITION BY cell ORDER BY r) AS k, cell IN (SELECT cell FROM covered) AS old, r FROM pool),
  main AS (
    SELECT item_id FROM ranked WHERE NOT is_gold ORDER BY old, k, r LIMIT p_size - v_gold),
  gold AS (
    SELECT item_id FROM ranked WHERE is_gold ORDER BY r LIMIT v_gold),
  chosen AS (
    SELECT item_id, row_number() OVER (ORDER BY random()) AS pos FROM (SELECT item_id FROM main UNION ALL SELECT item_id FROM gold) u)
  INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap)
  SELECT v_id, item_id, v_email, pos, false FROM chosen;
  RETURN v_id;
END $$;

-- The next owner batch of a curation queue, in the queue's order (12.7).
CREATE FUNCTION review.owner_next_queue_batch(p_export text, p_queue text, p_size int)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path = review, pg_temp AS $$
DECLARE
  v_email text := review.current_email();
  v_vocab text;
  v_id text;
BEGIN
  IF NOT review.is_owner() THEN RAISE EXCEPTION 'owner only'; END IF;
  IF p_size < 1 OR p_size > 100 THEN RAISE EXCEPTION 'curation batches have 1 to 100 items'; END IF;
  SELECT vocabulary INTO v_vocab FROM review.item WHERE export_version = p_export AND queue = p_queue LIMIT 1;
  IF v_vocab IS NULL THEN RAISE EXCEPTION 'no % queue in %', p_queue, p_export; END IF;
  SELECT 'b-' || to_char(now(), 'YYYYMMDD') || '-' || lpad((count(*) + 1)::text, 2, '0') INTO v_id
    FROM review.batch WHERE batch_id LIKE 'b-' || to_char(now(), 'YYYYMMDD') || '-%';
  INSERT INTO review.batch (batch_id, vocabulary, kind, description, sampling_spec, status)
  VALUES (v_id, v_vocab, 'curation', format('owner curation batch of %s from the %s queue of %s', p_size, p_queue, p_export),
          jsonb_build_object('kind', 'curation', 'export', p_export, 'queue', p_queue, 'order', 'item_id', 'size', p_size,
                             'built_by', 'review.owner_next_queue_batch'), 'open');
  INSERT INTO review.assignment (batch_id, item_id, reviewer_email, position, is_overlap)
  SELECT v_id, item_id, v_email, row_number() OVER (ORDER BY item_id), false FROM (
    SELECT item_id FROM review.item i WHERE export_version = p_export AND queue = p_queue
      AND NOT EXISTS (SELECT 1 FROM review.assignment s WHERE s.item_id = i.item_id) ORDER BY item_id LIMIT p_size) q;
  RETURN v_id;
END $$;

REVOKE ALL ON FUNCTION review.owner_next_batch(text, int, double precision), review.owner_next_queue_batch(text, text, int) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION review.owner_next_batch(text, int, double precision), review.owner_next_queue_batch(text, text, int) TO authenticated;

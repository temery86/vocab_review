-- Topic batches that mix survey and register items (Tom Emery, 31 October 2026). A batch may hold items of both
-- vocabularies. Each item keeps its own vocabulary, which decides its card, its grade wording and the repository its
-- answers are exported to.
ALTER TABLE review.batch DROP CONSTRAINT IF EXISTS batch_vocabulary_check;
ALTER TABLE review.batch ADD CONSTRAINT batch_vocabulary_check CHECK (vocabulary IN ('scv', 'rvv', 'mixed'));

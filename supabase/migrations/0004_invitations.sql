-- Invitations (V-10). When a reviewer was invited and the provider's message id, written by tools/invite_reviewers.py
-- with the service rights. Reviewers can read their own row as before and cannot change it.
ALTER TABLE review.reviewer ADD COLUMN IF NOT EXISTS invited_at timestamptz;
ALTER TABLE review.reviewer ADD COLUMN IF NOT EXISTS invite_message_id text;

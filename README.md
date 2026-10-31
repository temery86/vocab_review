# Vocabulary review

Expert review site for the survey (`scv`) and register (`rvv`) vocabularies. Build instructions in `CLAUDE.md`, decisions in `audit/DECISIONS.md`. Working title per V-01.

The repository holds no review data and no secret. Review content lives in Supabase and is read only after sign in.

## Layout

| Path | What |
|---|---|
| `supabase/migrations/` | Schema `review`, row level security, the reviewer item view, owner actions |
| `tests/` | Supabase shim for local Postgres, fictional seed, RLS tests (`gen_rls.py` writes `rls.sql`, `run_rls.py` runs it), tools end to end test |
| `schema/item.schema.json` | The item file contract (V-08) |
| `tools/` | `make_reviewers.py`, `load_items.py`, `make_batch.py`, `export_reviews.py`, `analyse_reviews.py` (V-09) |
| `web/` | Front end, Vite and plain TypeScript (V-05). Demo mode with fictional data at `?demo` or when no Supabase settings are given |
| `reports/` | RLS test report, tools end to end report, front end check report with screenshots |

## Running the checks locally

Needs docker (colima here), Python 3.12 and Node 20.

```
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python tests/run_rls.py           # RLS tests, writes reports/rls-test-report.md
.venv/bin/python tests/run_tools_e2e.py     # tools on fictional data, writes reports/tools-e2e-report.md
cd web && npm ci && npm run build && npm run check   # front end checks, writes reports/frontend-check-report.md
cd web && npm run dev                        # the site at http://localhost:5173/?demo
```

## Going live (Tom Emery, V-02)

1. Create the Supabase project in Frankfurt. Put the project URL, anon key, service key and the database connection string in `.env` (copy `.env.example`). Never commit it.
2. In the SQL editor run `supabase/migrations/0001_review_schema.sql` and `0002_owner_actions.sql`, in that order. Do not run `tests/supabase_shim.sql` or `tests/seed.sql` there.
3. Settings, API. Add `review` to the exposed schemas.
4. Authentication. Turn off new user sign ups. Keep email sign in. In the email template for the magic link, show the code with `{{ .Token }}` so reviewers get six digits rather than a link. Set the site URL to the GitHub Pages address.
5. Add yourself as owner. Write a small CSV outside any repository with columns `email,name,affiliation,expertise,programmes,role,consent_acknowledgement` and run `.venv/bin/python tools/make_reviewers.py <csv>`.
6. Load the vocabularies. `.venv/bin/python tools/load_items.py ../scv --export scv-review-0.3.0` and `.venv/bin/python tools/load_items.py ../register-corpus --export rvv-review-0.1.0`.
7. Front end. Create the GitHub repository, set repository variables `SUPABASE_URL` and `SUPABASE_ANON_KEY`, set Pages to deploy from GitHub Actions, and push `main`. Locally, `web/.env.local` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` runs the site against the project.
8. Sign in, open Admin, and build an owner batch from either vocabulary (stop point 4, the owner pilot).

V-10 (custom SMTP, privacy note reviewed, paid tier, a pilot with friendly reviewers, a tagged reviewer list) comes before anyone else is invited.

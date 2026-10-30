# Vocabulary Review Site

## Build instructions for the expert review website

Version 0.1, 26 October 2026. Owner Tom Emery. Independent project, not affiliated with ODISSEI.

This file is the working instruction set for Claude Code. It describes a small website through which invited experts review samples of vocabulary entries (an item shown against its construct, with its comparability grade), and through which the owner exports every review and comment for analysis. Read it in full before starting. Stop at each stop point and wait for a recorded decision, as in `../scv/CLAUDE.md`. The audit log, decision register and run report rules of `../scv/CLAUDE.md` section 3 apply here unchanged.

---

## 1. Purpose

The site is a measurement instrument, not a curation tool. Its job is to estimate the quality of each vocabulary by stratum and to surface systematic gaps, from small batches of reviews by data collection experts and area experts. Not every entry is reviewed. Fixes found through review are made in the vocabulary pipelines, not in the site.

---

## 2. Architecture

Two parts.

1. A static front end, built with Vite and plain TypeScript, deployed to GitHub Pages by a GitHub Action. It contains no review data. Anyone can load the empty shell, which is acceptable because GitHub Pages sites outside GitHub Enterprise Cloud cannot be made private.
2. A Supabase project as the backend, in the EU (Frankfurt) region. It holds reviewers, items, batches, assignments, responses and comments in Postgres, and handles sign in. Row level security decides who sees what. The front end uses the public anon key, which is safe only because every table has row level security enabled with no exceptions.

Review content (question text, definitions, grades) is loaded from Supabase only after a reviewer has signed in, and only for items assigned to that reviewer. Nothing from the vocabularies is committed to the front end repository.

Repositories.

- `review-site/` (this repository) holds the front end, the database schema and migrations, row level security policies and their tests. It may be public, since it holds no data and no secrets.
- `../scv/pipeline/80_review/` and later `../register-corpus/pipeline/80_review/` hold the scripts that build batches from each vocabulary's export and pull reviews back. Those scripts use the Supabase service key from a gitignored `.env`. The service key never appears in the front end, in this repository or in any log.

---

## 3. Sign in and access

- Email one time code, six digits, through Supabase Auth with `shouldCreateUser: false`. Use a code rather than a magic link, because institutional mail filters often open links before the recipient does and consume them.
- Public sign up is disabled. A reviewer exists only if the owner has added their email to the `reviewer` table and created the matching auth user with the admin API (`make_reviewers.py`). Any other address receives no code and sees a neutral message.
- Two roles. `reviewer` sees only their own assignments and responses. `owner` (one email, Tom's) sees everything and can export from the admin page.
- Custom SMTP is required. Supabase's built in mail service only delivers to members of the project's own team and is limited to two messages per hour. Configure a transactional provider (Brevo, Postmark or Resend) on a sending domain the owner controls, with SPF, DKIM and DMARC set. Record the choice as decision V-03.
- Free Supabase projects pause after a week without activity. During an active review round, either move the project to the paid tier or accept that the owner restores it from the dashboard. Record the choice as decision V-04.

---

## 4. Data model

All tables in schema `review`, with row level security on every table.

```
reviewer(
  email text primary key,
  name text not null,
  affiliation text,
  expertise text[],             -- area tags, for example health, labour, family
  programmes text[],            -- programme or country codes they know, for example ess, liss, dk
  role text check (role in ('reviewer','owner')) default 'reviewer',
  consent_acknowledgement bool default false,  -- may be named in acknowledgements
  active bool default true,
  created_at timestamptz default now())

item(
  item_id text primary key,     -- <vocabulary>:<measure_pid>:<construct_pid>:<export_version>
  vocabulary text not null,     -- scv, rvv
  export_version text not null, -- for example scv-0.2.0
  construct_pid text not null,
  construct_label text not null,
  construct_definition text not null,
  construct_exclusions text,
  measure_pid text not null,
  programme text not null,      -- or country and body for registers
  waves text,                   -- human readable coverage
  question_text text,           -- or definition text for registers
  question_text_en text,
  text_kind text,               -- question, definition
  response_categories jsonb,
  universe_text text,
  anchor_measure_pid text,
  anchor_question_text text,
  anchor_response_categories jsonb,
  grade text,                   -- identical, equivalent, related, null if not graded
  grade_reasons jsonb,
  method text,                  -- poc_full, poc_lowcost, production
  model_confidence real,
  neighbour_constructs jsonb,   -- five nearest constructs, pid and label, for the better construct choice
  stratum jsonb not null,       -- the sampling cell this item was drawn from
  is_gold bool default false,
  gold_belongs text,            -- known answer for gold items
  gold_grade text,
  created_at timestamptz default now())

batch(
  batch_id text primary key,    -- b-<yyyymmdd>-<nn>
  vocabulary text not null,
  description text,
  sampling_spec jsonb not null, -- strata, sizes, seed, overlap share, gold count
  status text check (status in ('draft','open','closed')) default 'draft',
  created_at timestamptz default now(),
  closes_at timestamptz)

assignment(
  assignment_id bigint generated always as identity primary key,
  batch_id text references batch,
  item_id text references item,
  reviewer_email text references reviewer,
  position int not null,
  is_overlap bool default false,
  unique (batch_id, item_id, reviewer_email))

response(                        -- append only, latest row per assignment is current
  response_id bigint generated always as identity primary key,
  assignment_id bigint references assignment,
  belongs text check (belongs in ('yes','no','unsure')),
  better_construct_pid text,    -- chosen from neighbour_constructs
  better_construct_text text,   -- free text when none fits
  grade_ok text check (grade_ok in ('yes','no','unsure','not_shown')),
  correct_grade text check (correct_grade in ('identical','equivalent','related','distinct')),
  comment text,
  seconds_on_item int,
  client_version text,
  submitted_at timestamptz default now())

batch_comment(                   -- free comments at the end of a batch
  comment_id bigint generated always as identity primary key,
  batch_id text references batch,
  reviewer_email text references reviewer,
  missing_constructs text,      -- constructs the reviewer expected and did not see
  systematic_issues text,
  other text,
  submitted_at timestamptz default now())
```

Row level security policies.

- `item`. A reviewer can select an item only if an assignment for it names their email in an open batch. The owner selects all.
- `assignment`. A reviewer selects their own rows. Only the owner, through the service key, inserts.
- `response`. A reviewer inserts rows only for their own assignments in open batches, and selects only their own rows. No updates or deletes for anyone. A changed answer is a new row.
- `batch_comment`. As `response`.
- `reviewer`. A reviewer selects only their own row. The owner selects all.
- Gold item fields `is_gold`, `gold_belongs` and `gold_grade` are never returned to reviewers. Expose items to reviewers through a view that omits them, and grant reviewers access to the view only.

Write `tests/rls.sql` covering every policy, including a reviewer trying to read another reviewer's assignments, items in a closed batch and gold fields, and a reviewer trying to update a response. Every policy test must pass before any real reviewer is added.

---

## 5. Reviewer experience

Simple and elegant. One idea per screen, generous whitespace, no decoration. A neutral identity for the project, independent of any institution. Two typefaces at most, one quiet accent colour, light and dark themes, readable at phone width, keyboard operable throughout.

Screens.

1. Sign in. Email field, then code field. One line explaining what the site is and who runs it, one line on how responses are used, a link to the privacy note.
2. Home. The reviewer's open batches with progress, for example 12 of 25, and a resume button. Closed batches listed below as completed.
3. Brief. Shown once per batch before the first item. What a construct is, what the grades mean (with one example of each), how long the batch takes (about fifteen minutes for 25 items), and that "unsure" is a valid answer.
4. Review item. Two cards side by side on wide screens, stacked on narrow ones.
   - Construct card. Label, definition, exclusions.
   - Item card. Programme, waves, question text in the canonical language with the English version beneath where held, response categories, universe.
   - Question 1. Does this item measure this construct? Yes, No, Unsure. If No, a short list of the five neighbouring constructs to choose from, plus "none of these" with a free text field.
   - Question 2, shown only when the item is graded and is not the anchor. The anchor item is shown in a third compact card. Is the grade right? The grade is shown with its one line meaning and the reasons recorded for it. Yes, No, Unsure. If No, pick the correct grade.
   - Optional comment field, collapsed by default.
   - Keyboard. Y, N and U answer the visible question, 1 to 5 pick a neighbour, Enter goes to the next item, Backspace goes back.
   - Every answer is saved as it is made, so closing the tab loses nothing.
5. End of batch. Three optional free text boxes (constructs you expected and did not see, systematic problems, anything else), then thanks.

Owner screens, visible only to the owner role.

6. Admin. Batches with status and completion per reviewer, a button to open or close a batch, and export buttons (section 7).

Gold items look identical to others. They are never revealed to reviewers.

---

## 6. Batches and sampling

Batches are built offline by `pipeline/80_review/make_batch.py` in each vocabulary repository, from that vocabulary's committed export, and pushed to Supabase with the service key. Each run is logged in that repository's audit log with its seed and specification.

- Stratify by vocabulary, programme or country, construct type, grading method, grade and model confidence band. Oversample the cells where errors are known to cluster. For the survey vocabulary, from the breadth run check, that is battery items under broad constructs, reference periods derived by the small model, and documented recodes graded as related.
- Route items to reviewers by `programmes` for data collection experts and by `expertise` for area experts.
- Batch size 20 to 30 items per reviewer.
- Overlap. 15 percent of items in a batch are also assigned to a second reviewer, for agreement.
- Gold items. Two or three per batch with known answers, drawn from the adjudicated constructs and the agent checks already done, rotated so no reviewer sees the same gold item twice.
- The sampling specification, including the seed, is stored in `batch.sampling_spec` and in the vocabulary repository, so any batch can be rebuilt exactly.

---

## 7. Export

Exports are the point of the site and must be complete, repeatable and lossless.

- `pipeline/80_review/export_reviews.py` in each vocabulary repository pulls, with the service key, every response row (not only the latest), every batch comment, the items and assignments they refer to, and the batch specifications. It writes them to `reviews/exports/<yyyy-mm-dd-hhmm>/` as CSV and as JSON lines, one file per table plus one joined file (`reviews_joined.csv`) with one row per current response and every item field beside it. A `codebook.md` describing every column is written beside them.
- Reviewer emails are replaced by a stable pseudonym (`r01`, `r02` and so on) in the joined file, with the key kept in a separate `reviewers_key.csv` that is gitignored. Exports committed to a vocabulary repository contain pseudonyms only.
- Every export run is an audit event with counts per table.
- The owner admin page offers the same joined CSV and the comments as CSV for a quick look. The script remains the record.
- A nightly GitHub Action is not used for exports, because exports contain personal data and belong on the owner's machine. Supabase is the live store, and exports to the owner's machine are the backup. Run an export at the close of every batch.

---

## 8. Analysis

`pipeline/80_review/analyse_reviews.py` reads an export and writes `reports/review-<date>.md`.

- Membership precision per stratum, with Wilson 95 percent intervals. Unsure answers are reported separately and excluded from the denominator.
- Grade accuracy per stratum and per grade, with intervals.
- Agreement on overlap items, Cohen's kappa for membership and for grade.
- Gold item accuracy per reviewer. A reviewer below an agreed level is flagged and their responses are reported with and without them.
- Gap detection. Free text better construct answers and missing construct comments are embedded with the vocabulary's pinned embedding model and clustered. Clusters with answers from more than one reviewer are listed as candidate systematic gaps.
- Error patterns. Wrong answers are cross tabulated by grading method, construct type, programme and pair rule, so a fix can be aimed at the pipeline step that caused it.
- The quality threshold is fixed before the first batch (decision V-06). The report states for each stratum whether the lower bound of its interval clears the threshold.

---

## 9. Privacy

Reviewers' names, emails and comments are personal data. The sign in page links to a short privacy note stating who runs the site, what is stored, that Supabase in the EU stores it, how long it is kept, that comments may be quoted without attribution in publications, and that reviewers are named in acknowledgements only with their consent (`consent_acknowledgement`). Reviewers can ask for their data to be deleted, which the owner does by hand.

Question text from programmes with restrictive documentation terms is shown only to signed in reviewers, as internal expert review. It is never placed in the front end repository or on any public page.

---

## 10. Phases and stop points

### Phase 0. Decisions

Open the decision register `audit/DECISIONS.md` with these as pending, and halt.

- V-01 Project name and the domain or GitHub Pages address for the site.
- V-02 Supabase project and region (EU, Frankfurt proposed).
- V-03 SMTP provider and sending domain.
- V-04 Supabase tier during review rounds (paid tier, or free with manual restore).
- V-05 Front end stack (Vite with plain TypeScript proposed, no framework).
- V-06 Quality threshold. Proposal is membership precision of at least 95 percent and grade accuracy of at least 85 percent per stratum, judged on the lower bound of the 95 percent interval.
- V-07 Batch size, overlap share and gold items per batch (25, 15 percent and 3 proposed).

**Stop point 0.**

### Phase 1. Backend

Supabase schema, view for reviewers, row level security policies, admin scripts `make_reviewers.py` and a seed script with fictional reviewers and fictional items for testing. All RLS tests pass against the seed data.

**Stop point 1.** Owner checks the RLS test report and signs in as a seeded test reviewer.

### Phase 2. Front end

Screens 1 to 6 against the seeded data. Deployed to GitHub Pages from the main branch by a GitHub Action. Checked at phone and desktop widths, with keyboard only, and in both themes. An accessibility check with an automated tool and by hand on the review screen.

**Stop point 2.** Owner reviews the site on the seeded data.

### Phase 3. Batch and export tooling

`make_batch.py`, `export_reviews.py` and `analyse_reviews.py` in `../scv/pipeline/80_review/`, tested end to end on a batch of fictional responses. The export round trips without loss (every response row in Supabase appears in the export, counts match).

**Stop point 3.**

### Phase 4. Pilot

One real batch of 15 items from the survey vocabulary sent to two or three friendly reviewers. Collect their comments on the instructions, layout and timing. Fix what they find.

**Stop point 4.** Owner decides whether the instrument is ready.

### Phase 5. Review rounds

Batches built, opened, exported at close and analysed, round by round. Each round's report goes to the owner, and fixes go back to the vocabulary pipelines as tracked tasks.

---

## 11. Working rules

- Nothing from a vocabulary is committed to this repository. Seed data is fictional.
- No secret appears in the front end, in this repository, or in any log. The service key lives only in gitignored `.env` files on the owner's machine.
- Row level security is enabled on every table before any data is loaded, and the RLS tests run in CI on every change to the schema.
- Response rows are never updated or deleted by the application.
- Every batch build and every export is an audit event in the vocabulary repository it belongs to.
- Prose in reports without em dashes, semicolons or colons.

---

## 12. Amendment 1. Two vocabularies, owner first, and stop point 0 decided

Tom Emery, 30 October 2026. Where this section and sections 1 to 11 differ, this section applies. Open `audit/DECISIONS.md` with V-01 to V-07 as decided below and V-08 to V-10 added, write one `type: decision` audit event per decision, and start phase 1. Stop point 0 is taken by this section.

### 12.1 Stop point 0 decisions

- V-01 Name and address. The project name is not chosen yet. The site uses the working title "Vocabulary review" set in one configuration file, and the default GitHub Pages address of the repository. Changing the name later is a configuration change only.
- V-02 Supabase project in the EU (Frankfurt) region. Tom Emery creates the account and the project himself and puts the URL and keys in the gitignored `.env`. The agent never handles his passwords and never signs in on his behalf.
- V-03 SMTP deferred. While Tom Emery is the only reviewer, the built in Supabase mail is used, which delivers to members of the project's own team. Custom SMTP on a domain he controls is set up before the first invited reviewer (V-10).
- V-04 Free tier while Tom Emery reviews alone. Paid tier from the first external round.
- V-05 Vite with plain TypeScript, no framework.
- V-06 Quality threshold. Membership precision at least 95 percent and grade accuracy at least 85 percent per stratum, on the lower bound of the 95 percent interval. Applied to external rounds. Owner rounds are reported against it but not judged by it (12.4).
- V-07 Batch size 25 for invited reviewers with 15 percent overlap and 3 gold items. For the owner the batch size can be set from 25 to 100 per batch, overlap is off, and gold items are 3 per 25.
- V-08 Item files as the contract between vocabularies and the site (12.3).
- V-09 Batch, export and analysis tools live in this repository (12.5), not in each vocabulary repository.
- V-10 Before the first invited reviewer. Custom SMTP with SPF, DKIM and DMARC, the privacy note, the paid tier, a pilot with two or three friendly reviewers, and a reviewer list with expertise and programme tags. This is a stop point.

### 12.2 Vocabularies

Two vocabularies in version one of the site, `scv` (survey) and `rvv` (register). The policy intervention vocabulary is added later by its own amendment. Each vocabulary has its own brief screen, its own item card and its own grade wording.

- Survey item card. As section 5.
- Register item card. Variable name and label in the national language with the English gloss beneath, definition with its kind (office, recovered, label only), register, body and country, years covered, classification and version, population, reference timing. A provisional link is not marked as such to the reviewer, so that the answer is not biased, but it is recorded in the stratum.
- Construct card for both. Label, definition, and the definition provenance in small type (person written, draft accepted, draft generated).
- Question 1 for both. Does this item belong to this construct. Yes, no, unsure, with the five neighbouring constructs on no.
- Question 2 for graded items of either vocabulary, with the anchor item in a compact card. Register grades are shown with the register attribute reasons.

### 12.3 Item file format

Each vocabulary writes `review/items/<export_version>.jsonl` and `review/gold/<export_version>.jsonl` in its own repository. One JSON object per item with the fields of the `item` table in section 4, plus `context`, an object of named fields shown on the item card in the order given, with labels from a per vocabulary display map in the front end. The register vocabulary puts its card fields in `context`. Changes to the `item` table in section 4.

- `measure_pid` holds the represented variable PID for register items.
- New column `context jsonb`.
- New column `construct_definition_provenance text`.
- `method` values extended with `poc_lowcost_v2` and the register methods.
- `item_id` keeps the form `<vocabulary>:<measure_pid>:<construct_pid>:<export_version>`.

The loader validates every line against a JSON schema in `schema/item.schema.json` and refuses a file with any invalid line.

### 12.4 Owner rounds

- Tom Emery is a reviewer with role owner. His responses are stored like any other and pseudonymised as `r00` in exports.
- Analysis reports owner rounds separately from invited rounds and never pools them for the headline estimates, because he adjudicated many of the constructs under review. Owner rounds are for finding and fixing errors.
- Owner batches can be built continuously (a new batch of the chosen size on request from the admin screen, drawing from strata not yet covered), so review can go on without rebuilding batches by hand.
- Gold accuracy is still reported for the owner, so drift over long sessions is visible.
- The end of batch screen is kept but its three boxes are optional and collapsed for the owner.

### 12.5 Tools in this repository

`tools/load_items.py`, `tools/make_batch.py`, `tools/export_reviews.py` and `tools/analyse_reviews.py` replace the per vocabulary scripts of sections 6 to 8. Each takes the vocabulary repository path as an argument, reads its item and gold files, uses the service key from `.env`, and writes an audit event into that vocabulary repository's audit log as well as this repository's. Exports and reports go to `review/exports/` and `reports/` in the vocabulary repository the reviews belong to, as section 7.

### 12.6 Order of work

1. Phase 1 backend and phase 2 front end on fictional seed data, for both vocabularies, with the RLS tests. These do not wait for the vocabularies.
2. Phase 3 tools, tested end to end on fictional data.
3. Load the real item files when the survey (D-35) and register (R-29) exports exist. Either can be loaded first.
4. Stop point 4 becomes the owner pilot. Tom Emery reviews one batch from each vocabulary and records what to change. Then owner rounds run.
5. V-10 before anyone else is invited.

### 12.7 Curation queues (amendment 1, added 30 October 2026, 21:30)

Besides quality samples, a vocabulary can offer curation queues, every item of a queue rather than a sample, from `review/queues/<export_version>/<queue>.jsonl`. They are for decisions that must be made on every item (where a variable belongs, whether a noted member moves). Curation items show the construct and the five neighbours as usual, and add two answers to question 1, "belongs in a neighbour" (pick one) and "reject" (with a reason from a list given in the queue file). A membership item shows the construct with its members and the note, and asks per named member stay, move or reject. Curation batches are built in the queue's order, not by stratified sampling, for the owner first. Answers are exported like any other and applied by the vocabulary's own apply step. The site never edits a vocabulary. Curation answers are not used for quality estimates, and quality sample items are never drawn from an open queue.

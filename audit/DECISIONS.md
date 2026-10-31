# Decision register, vocabulary review site

Decisions V-01 to V-07 were taken by Tom Emery on 30 October 2026 in amendment 1 (`CLAUDE.md` section 12.1), which takes stop point 0. V-08 to V-10 were added by the same amendment.

## V-01 Name and address
Status. Decided.
Choice. The project name is not chosen yet. The site uses the working title "Vocabulary review" set in one configuration file, and the default GitHub Pages address of the repository. Changing the name later is a configuration change only.
Decided by. Tom Emery on 2026-10-30.

## V-02 Supabase project and region
Status. Decided.
Choice. Supabase project in the EU (Frankfurt) region. Tom Emery creates the account and the project himself and puts the URL and keys in the gitignored `.env`. The agent never handles his passwords and never signs in on his behalf.
Decided by. Tom Emery on 2026-10-30.

## V-03 SMTP
Status. Decided.
Choice. SMTP deferred. While Tom Emery is the only reviewer the built in Supabase mail is used, which delivers to members of the project's own team. Custom SMTP on a domain he controls is set up before the first invited reviewer (V-10).
Decided by. Tom Emery on 2026-10-30.

## V-04 Supabase tier
Status. Decided.
Choice. Free tier while Tom Emery reviews alone. Paid tier from the first external round.
Decided by. Tom Emery on 2026-10-30.

## V-05 Front end stack
Status. Decided.
Choice. Vite with plain TypeScript, no framework.
Decided by. Tom Emery on 2026-10-30.

## V-06 Quality threshold
Status. Decided.
Choice. Membership precision at least 95 percent and grade accuracy at least 85 percent per stratum, on the lower bound of the 95 percent interval. Applied to external rounds. Owner rounds are reported against it but not judged by it (section 12.4).
Decided by. Tom Emery on 2026-10-30.

## V-07 Batch size, overlap and gold
Status. Decided.
Choice. Batch size 25 for invited reviewers with 15 percent overlap and 3 gold items. For the owner the batch size can be set from 25 to 100 per batch, overlap is off, and gold items are 3 per 25.
Decided by. Tom Emery on 2026-10-30.

## V-08 Item files as the contract
Status. Decided.
Choice. Item files are the contract between the vocabularies and the site (section 12.3). Each vocabulary writes `review/items/<export_version>.jsonl` and `review/gold/<export_version>.jsonl`, and curation queues in `review/queues/<export_version>/` (section 12.7). The loader validates every line against `schema/item.schema.json` and refuses a file with any invalid line.
Decided by. Tom Emery on 2026-10-30.

## V-09 Tools in this repository
Status. Decided.
Choice. `tools/load_items.py`, `tools/make_batch.py`, `tools/export_reviews.py` and `tools/analyse_reviews.py` live in this repository and take the vocabulary repository path as an argument, replacing the per vocabulary scripts of sections 6 to 8.
Decided by. Tom Emery on 2026-10-30.

## V-10 Before the first invited reviewer
Status. Decided, a stop point.
Choice. Before anyone else is invited. Custom SMTP with SPF, DKIM and DMARC, the privacy note, the paid tier, a pilot with two or three friendly reviewers, and a reviewer list with expertise and programme tags.
Decided by. Tom Emery on 2026-10-30.

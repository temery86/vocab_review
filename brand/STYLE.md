# Style guide, vocabulary review site

Tom Emery, 30 October 2026. Applies to every screen of the review site. Tokens are in `brand/tokens.css`, logos in `brand/logos/`. This guide replaces the line "a neutral identity for the project, independent of any institution" in section 5 of `CLAUDE.md`. The site keeps its own neutral name and look, and carries subtle SSHOC-NL and Macroscope branding as the infrastructures that support it. It carries no ODISSEI mark.

## 1. Principles

1. The site is a measurement instrument. Nothing in its look may push a reviewer towards an answer. Branding stays at the edges of the page and never touches the review content.
2. Quiet and readable. One typeface family, one interactive colour, generous whitespace, no decoration.
3. Subtle branding means three things only. A thin rule in Macroscope red at the very top of every page, SSHOC-NL blue as the single interactive colour, and both logos small in the footer and on the sign in screen.
4. Accessible. WCAG 2.2 AA at least, every pairing in `tokens.css` is checked, keyboard operable throughout, light and dark themes.

## 2. Colour

| Token | Light | Dark | Use |
|---|---|---|---|
| `--brand-navy` | #223C87 | | SSHOC-NL blue, sampled from the logo |
| `--brand-red` | #FF0F48 | | Macroscope red, sampled from the logo. Decorative only |
| `--bg` | #FFFFFF | #12151C | Page |
| `--surface` | #F6F7FA | #191D26 | Panels, footer, card backgrounds behind content |
| `--surface-raised` | #FFFFFF | #1E2330 | Cards |
| `--border` | #DDE1EA | #2C3242 | Hairlines, card borders |
| `--text` | #1A1D24 | #E8EAF0 | Body text |
| `--text-muted` | #5A6070 | #9AA0AE | Labels, metadata, provenance |
| `--accent` | #223C87 | #9DB0EC | Buttons, links, selected answers, progress, focus |
| `--warning` | #B4530B | #F0A35E | Sign in problems, failed saves, connection lost |

Rules.

- Macroscope red is never used for text, buttons, links or any state. At 3.9 to 1 on white it is not readable as small text, and red reads as wrong. It appears only as the top rule (3 px, full width) and in the Macroscope logo.
- SSHOC-NL blue is the only interactive colour. In dark mode the lighter tint `--accent` replaces it, because the logo blue is too dark on a dark page.
- No green and no red for any state. Errors and warnings use the amber `--warning`. Success is shown with the accent colour and a short text, such as "Saved".
- Grades (identical, equivalent, related, distinct) use the one hue ramp `--grade-*`, from dark to light. It is ordinal, not good to bad. Each grade chip also shows the grade name, so colour never carries meaning alone.

## 3. Typography

- One family, Ubuntu Sans, which matches the SSHOC-NL type and is open (Ubuntu Font Licence). Ubuntu Sans Mono for PIDs, variable names and codes.
- Self host the fonts from the package (for example the Fontsource variable packages for Ubuntu Sans and Ubuntu Sans Mono) and bundle them with the build. Do not load fonts from Google's servers, because that sends reviewers' addresses to a third party.
- Scale from `tokens.css`. Body 16 px with line height 1.55. Question text on the item card 18 px, because it is the thing being judged. Page titles 28 px, section titles 22 px, labels and metadata 13 to 14 px in `--text-muted`.
- Weights. 400 for text, 500 for labels and buttons, 600 for titles. No italics for emphasis in review content, since question texts may contain their own.
- Question texts and definitions keep their original language, capitalisation and punctuation. Never truncate them on the review screen.

## 4. Layout and components

- Content width at most 1100 px, centred, with 16 px side gutters at phone width and no horizontal scroll.
- Spacing on the 4 px scale in `tokens.css`. 24 px between cards, 16 px inside them.
- Cards. `--surface-raised`, 1 px `--border`, radius 8 px, light shadow in light mode only. The construct card and the item card sit side by side from 900 px width, stacked below it, construct first.
- Answer buttons. Yes, No and Unsure are the same size, the same neutral style (outlined, `--text` on `--surface-raised`) and in a fixed order. The selected answer fills with `--accent`. Never colour yes and no differently. Keyboard hints (Y, N, U, 1 to 5) in small muted mono beside each label.
- Neighbour constructs on No. A plain list with the number key, label and the first line of the definition.
- Grade question. The grade as a chip with its name, its one line meaning, and the reasons as a short list in muted text.
- Provenance (definition provenance, method, export version) in 13 px muted text at the foot of the card it belongs to.
- Progress. A thin bar in `--accent` with "12 of 25" beside it.
- Focus ring 2 px `--focus`, offset 2 px, on every interactive element.
- Motion. None beyond a 120 ms fade between items, switched off under reduced motion.

## 5. Branding placement

| Place | What |
|---|---|
| Top of every page | A 3 px full width rule in `--brand-red`, above the header |
| Header | The site name (working title "Vocabulary review", set in config, V-01) in 18 px, weight 600, `--text`. No logo in the header |
| Footer, every page | A `--surface` band with the line "Supported by SSHOC-NL and Macroscope" (wording in config, for Tom Emery to confirm) and the two logos, each 24 px high, SSHOC-NL first, 32 px apart |
| Sign in screen | The two logos at 28 px high, centred below the form, under the same line |
| Review screen | No logos and no brand colour other than the top rule and the accent |
| Favicon | A neutral glyph in `--brand-navy`, not either logo |

Logo rules.

- Use the files in `brand/logos/`. `*-colour.png` on light backgrounds, `*-white.png` on dark backgrounds, switched with the theme.
- Clear space around each logo at least half its height. Minimum height 20 px.
- Never recolour, stretch, crop, outline or place a logo on a coloured fill. Never place one logo inside the other's area.
- The PNGs were made from the files Tom Emery supplied, with the white background removed. Replace them with the official SVGs from the SSHOC-NL and Macroscope communications teams when those arrive. The originals are kept beside them.
- Both logos link to the projects' public sites, opening in the same tab, with accessible names "SSHOC-NL" and "Macroscope".

## 6. Writing on the site

Plain, short sentences. No marketing language. No em dashes, semicolons or colons in prose. Sentence case for titles and buttons ("Next item", not "Next Item"). Instructions in the brief speak to the reviewer directly ("You will see an item and a construct").

## 7. Checks before stop point 2

- Every token pairing used for text checked against WCAG AA in both themes, with the results in the stop point report.
- Screenshots of the sign in screen, home, brief, review item (survey and register), end of batch and admin, at 375 px and 1280 px, in both themes.
- A check that no font, script or image is loaded from a third party host other than Supabase.

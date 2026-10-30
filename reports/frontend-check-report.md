# Front end check report

Run 2026-10-30 21:40 UTC by `web/tests/check.mjs` with headless Chromium (Playwright) on the demo build, which runs on fictional data in the browser. Accessibility by axe-core with the WCAG 2.1 A and AA rules. Sideways scroll is page width beyond the viewport. Screenshots in `screens/`. The manual check of the review screen is in the section below.

42 checks, 42 passed.

| Check | Result | Detail |
|---|---|---|
| sign in, phone, light | pass | no axe violations |
| privacy note, phone, light | pass | no axe violations |
| home, phone, light | pass | no axe violations |
| brief, phone, light | pass | no axe violations |
| survey item, graded, phone, light | pass | no axe violations |
| register item, phone, light | pass | no axe violations |
| curation placement, phone, light | pass | no axe violations |
| curation membership, phone, light | pass | no axe violations |
| end of batch, phone, light | pass | no axe violations |
| admin, phone, light | pass | no axe violations |
| sign in, phone, dark | pass | no axe violations |
| privacy note, phone, dark | pass | no axe violations |
| home, phone, dark | pass | no axe violations |
| brief, phone, dark | pass | no axe violations |
| survey item, graded, phone, dark | pass | no axe violations |
| register item, phone, dark | pass | no axe violations |
| curation placement, phone, dark | pass | no axe violations |
| curation membership, phone, dark | pass | no axe violations |
| end of batch, phone, dark | pass | no axe violations |
| admin, phone, dark | pass | no axe violations |
| sign in, desktop, light | pass | no axe violations |
| privacy note, desktop, light | pass | no axe violations |
| home, desktop, light | pass | no axe violations |
| brief, desktop, light | pass | no axe violations |
| survey item, graded, desktop, light | pass | no axe violations |
| register item, desktop, light | pass | no axe violations |
| curation placement, desktop, light | pass | no axe violations |
| curation membership, desktop, light | pass | no axe violations |
| end of batch, desktop, light | pass | no axe violations |
| admin, desktop, light | pass | no axe violations |
| sign in, desktop, dark | pass | no axe violations |
| privacy note, desktop, dark | pass | no axe violations |
| home, desktop, dark | pass | no axe violations |
| brief, desktop, dark | pass | no axe violations |
| survey item, graded, desktop, dark | pass | no axe violations |
| register item, desktop, dark | pass | no axe violations |
| curation placement, desktop, dark | pass | no axe violations |
| curation membership, desktop, dark | pass | no axe violations |
| end of batch, desktop, dark | pass | no axe violations |
| admin, desktop, dark | pass | no axe violations |
| keyboard only, sign in, open a batch, answer both questions, pick a neighbour, go back | pass | question 2 correct grade shown true, moved to #/b/b-demo-01/2, neighbour chosen 1, back to #/b/b-demo-01/1, 7 responses saved, focus outline solid |
| gold item looks like any other | pass | the page has no gold field or label |

## Check by hand of the review screen

Done by the agent on 30 October 2026 from the demo build, the page source and the screenshots, not by a person with assistive technology. A check by Tom Emery with a screen reader belongs to the owner pilot.

- Order and structure. One h1 per screen. On the review screen the construct and the item are articles with their own headings, questions are fieldsets with a legend, and the correct grade choices are a labelled group.
- Answers. Every choice is a button with aria-pressed, so its state is announced. The saved state is announced through a polite live region.
- Keyboard. Tab order follows the reading order. Y, N and U answer the question shown, 1 to 5 pick a neighbour, Enter goes on and Backspace goes back, and none of these keys act while a text field has focus. The focus outline is 3 pixels in a colour separate from the accent.
- Forms. Every input, select and textarea has a label, visible or for screen readers only. The sign in code field uses the one time code autocomplete.
- Width and themes. Cards sit side by side above 720 pixels and stack below. The register card's two columns become one below 480 pixels. Light and dark themes follow the system and can be switched, and the choice is remembered.
- Gold. Gold items carry no mark on the page, and the reviewer view of the database has no gold column.

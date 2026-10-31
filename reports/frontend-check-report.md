# Front end check report

Run 2026-10-30 22:01 UTC by `web/tests/check.mjs` with headless Chromium (Playwright) on the demo build, which runs on fictional data in the browser. Accessibility by axe-core with the WCAG 2.1 A and AA rules. Sideways scroll is page width beyond the viewport. Screenshots in `screens/`. The manual check of the review screen is in the section below.

44 checks, 44 passed.

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
| every text pairing reaches WCAG AA 4.5 to 1 in both themes | pass | 36 pairings, lowest 4.91 |
| no font, script or image from a third party host | pass | every request went to the site itself |

## Contrast of the token pairings used for text

| Theme | Use | Text | Background | Ratio | AA |
|---|---|---|---|---|---|
| light | body text on the page | --text #1A1D24 | --bg #FFFFFF | 16.87 | pass |
| light | text on the footer and panels | --text #1A1D24 | --surface #F6F7FA | 15.74 | pass |
| light | text on cards | --text #1A1D24 | --surface-raised #FFFFFF | 16.87 | pass |
| light | muted text on the page | --text-muted #5A6070 | --bg #FFFFFF | 6.28 | pass |
| light | muted text on the footer | --text-muted #5A6070 | --surface #F6F7FA | 5.87 | pass |
| light | muted text on cards | --text-muted #5A6070 | --surface-raised #FFFFFF | 6.28 | pass |
| light | links on the page | --accent #223C87 | --bg #FFFFFF | 10.17 | pass |
| light | links and outlines on cards | --accent #223C87 | --surface-raised #FFFFFF | 10.17 | pass |
| light | button and selected answer text | --on-accent #FFFFFF | --accent #223C87 | 10.17 | pass |
| light | button text on hover | --on-accent #FFFFFF | --accent-hover #1B3070 | 12.33 | pass |
| light | warnings on the page | --warning #B4530B | --bg #FFFFFF | 5.02 | pass |
| light | warnings on cards | --warning #B4530B | --surface-raised #FFFFFF | 5.02 | pass |
| light | text on a warning notice | --text #1A1D24 | --warning-tint #FBEFE5 | 14.92 | pass |
| light | text on the demo notice | --text #1A1D24 | --accent-tint #E9EDF8 | 14.40 | pass |
| light | identical chip | --chip-fg-identical #FFFFFF | --grade-identical #223C87 | 10.17 | pass |
| light | equivalent chip | --chip-fg-equivalent #FFFFFF | --grade-equivalent #4A62AE | 5.75 | pass |
| light | related chip | --chip-fg-related #1A1D24 | --grade-related #8394CC | 5.68 | pass |
| light | distinct chip | --chip-fg-distinct #1A1D24 | --grade-distinct #C3CBE6 | 10.44 | pass |
| dark | body text on the page | --text #E8EAF0 | --bg #12151C | 15.18 | pass |
| dark | text on the footer and panels | --text #E8EAF0 | --surface #191D26 | 14.02 | pass |
| dark | text on cards | --text #E8EAF0 | --surface-raised #1E2330 | 13.05 | pass |
| dark | muted text on the page | --text-muted #9AA0AE | --bg #12151C | 6.97 | pass |
| dark | muted text on the footer | --text-muted #9AA0AE | --surface #191D26 | 6.44 | pass |
| dark | muted text on cards | --text-muted #9AA0AE | --surface-raised #1E2330 | 5.99 | pass |
| dark | links on the page | --accent #9DB0EC | --bg #12151C | 8.57 | pass |
| dark | links and outlines on cards | --accent #9DB0EC | --surface-raised #1E2330 | 7.36 | pass |
| dark | button and selected answer text | --on-accent #12151C | --accent #9DB0EC | 8.57 | pass |
| dark | button text on hover | --on-accent #12151C | --accent-hover #B7C6F2 | 10.76 | pass |
| dark | warnings on the page | --warning #F0A35E | --bg #12151C | 8.79 | pass |
| dark | warnings on cards | --warning #F0A35E | --surface-raised #1E2330 | 7.55 | pass |
| dark | text on a warning notice | --text #E8EAF0 | --warning-tint #3A2A1C | 11.43 | pass |
| dark | text on the demo notice | --text #E8EAF0 | --accent-tint #222C48 | 11.47 | pass |
| dark | identical chip | --chip-fg-identical #12151C | --grade-identical #C3CBE6 | 11.31 | pass |
| dark | equivalent chip | --chip-fg-equivalent #12151C | --grade-equivalent #9DB0EC | 8.57 | pass |
| dark | related chip | --chip-fg-related #12151C | --grade-related #6F82C2 | 4.91 | pass |
| dark | distinct chip | --chip-fg-distinct #FFFFFF | --grade-distinct #45569A | 6.88 | pass |

## Check by hand of the review screen

Done by the agent on 30 October 2026 from the demo build, the page source and the screenshots, not by a person with assistive technology. A check by Tom Emery with a screen reader belongs to the owner pilot.

- Order and structure. One h1 per screen. On the review screen the construct and the item are articles with their own headings, questions are fieldsets with a legend, and the correct grade choices are a labelled group.
- Answers. Yes, No and Unsure are the same size and neutral style in a fixed order, with the selected one filled in the accent. Every choice is a button with aria-pressed. The saved state is announced through a polite live region, and a failed save shows in the warning amber.
- Keyboard. Tab order follows the reading order. Y, N and U answer the question shown, 1 to 5 pick a neighbour, Enter goes on and Backspace goes back, and none of these keys act while a text field has focus. The focus ring is 2 pixels in the focus token.
- Forms. Every input, select and textarea has a label, visible or for screen readers only. The sign in code field uses the one time code autocomplete.
- Width and themes. Cards sit side by side from 900 pixels and stack below, construct first. The register card's two columns become one below 480 pixels. Light and dark follow the system and can be switched, and the logos switch between the colour and white files with the theme.
- Gold. Gold items carry no mark on the page, and the reviewer view of the database has no gold column.

## Deviations from brand/STYLE.md

- Footer. The guide puts the footer with the logos on every page and no logos on the review screen. The review screen therefore has no footer. The sign in screen shows the logos below the form instead of in the footer, so they do not appear twice.
- Logo links. The guide asks for the logos to link to the projects' public sites. No dedicated public site for SSHOC-NL or Macroscope could be confirmed (both appear on partner and news pages only), so the addresses are empty in `web/src/config.ts` and the logos are shown unlinked, with their names as accessible labels, until Tom Emery fills them in.
- Neighbour constructs. The guide asks for the first line of each neighbour's definition. The item files carry the neighbour's PID and label only, so the label is shown. Adding a short definition to `neighbour_constructs` in the survey and register item builders would close this.
- Supporter line. "Supported by SSHOC-NL and Macroscope" is the guide's wording, kept in config for Tom Emery to confirm.
- Grade chip text. The guide gives the grade ramp but not the text colour on it. White or near black was chosen per grade and theme for contrast, and every chip passes AA (see the contrast table).
- Fonts are Ubuntu Sans and Ubuntu Sans Mono from the Fontsource variable packages, bundled with the build. No request leaves the site.

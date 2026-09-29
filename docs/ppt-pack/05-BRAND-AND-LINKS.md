# Brand, assets and final links

## Links to place in the deck

| Item | Link / file | Use |
|---|---|---|
| Live demo | https://saathi-drab.vercel.app | Slides 8 and 12; test the final QR before export |
| API | https://saathi-api-gm4i.onrender.com | Slide 12 small text or speaker notes; a sleeping free instance may need to wake |
| Repository | https://github.com/adityasinghin01-hash/saathi | Slide 12; [HANDOFF](../HANDOFF.md#live-29-sep-2026-10-am) calls it private, so verify judge access before export |
| Saathi logo | [frontend/public/art/logo.svg](../../frontend/public/art/logo.svg) | Use the original SVG at its natural proportions |
| Screenshot map | [03-SCREENSHOTS.md](03-SCREENSHOTS.md) | Use the supplied captures only; ignore S21 |
| Diagram source | [_build/diagrams.py](_build/diagrams.py) | Claude will render D1–D6; do not present the PDF as a separate product |

## Illustrations

Original image assets in `frontend/public/art/`:

| File | Suggested use |
|---|---|
| [home.webp](../../frontend/public/art/home.webp) | Home / patient context |
| [centre.webp](../../frontend/public/art/centre.webp) | PHC context |
| [shelf.webp](../../frontend/public/art/shelf.webp) | Stockout / shelf context |
| [van.webp](../../frontend/public/art/van.webp) | Transfer journey |
| [medkit.webp](../../frontend/public/art/medkit.webp) | Medicine handover |

Use these as illustrations, never as evidence that a vehicle, medicine or field clinic was photographed. Keep the screenshots' own **Synthetic demo data** label or add it beside a crop.

## Colours — exact light-theme CSS tokens

Source: [frontend/src/styles/saathi.css](../../frontend/src/styles/saathi.css). Use the light theme for the slides; do not approximate the hex values.

| Use | Token | Hex |
|---|---|---|
| Main background | `--paper` | `#fbf4ea` |
| Raised surface | `--paper-raised` | `#fffaf3` |
| Soft inset | `--paper-sunk` | `#f4e9da` |
| Main text | `--ink` | `#2e2119` |
| Secondary text | `--ink-muted` | `#6a5444` |
| Strong clay | `--clay-500` | `#bf5630` |
| Button/diagram clay | `--clay-600` | `#b04a24` |
| Dark clay | `--clay-700` | `#8f3a1b` |
| Light clay | `--clay-100` | `#f8e2d4` |
| Marigold | `--marigold-400` | `#f2a93b` |
| Light marigold | `--marigold-100` | `#fdefd3` |
| Leaf | `--leaf-400` | `#6d8a5a` |
| Light leaf | `--leaf-100` | `#e6eedc` |
| Out of stock text / background | `--status-out`, `--status-out-bg` | `#a3231b`, `#fbe4df` |
| Low stock text / background | `--status-low`, `--status-low-bg` | `#7a4d00`, `#fcefcf` |
| OK text / background | `--status-ok`, `--status-ok-bg` | `#0f635b`, `#dcefea` |
| Waiting text / background | `--status-wait`, `--status-wait-bg` | `#5e554e`, `#ece5dd` |
| Divider | `--line` | `#e8d9c6` |

## Type and bilingual copy

- Display: **Baloo 2** with **Baloo 2 Devanagari** fallback. Body: **IBM Plex Sans** with **IBM Plex Sans Devanagari** fallback. The exact CSS families are `--font-display`, `--font-sans` and `--font-hindi` in [saathi.css](../../frontend/src/styles/saathi.css).
- Keep **Hindi + English on every visible diagram and UI label**. Pair them directly, for example **Reported / रिपोर्ट दर्ज**, **Verify / जाँच**, **Approve / मंज़ूरी**, **Stock age / स्टॉक कब का**. For a crowded chart, use a bilingual legend keyed to compact symbols, not tiny Devanagari.
- The wordmark is **Saathi · साथी**. Retain the Hindi script; do not make “Hindi-first” claims from S21 or S23. S23 has a Hindi transcript while its interface language is English.
- Use sentence case and plain words. Medical terms such as “metformin” can keep their English spelling alongside the Hindi label.

## Label rules

1. Put **Synthetic demo data** on every slide with app screens, synthetic people, stock values, the Ramesh story or evaluation. If a screenshot crop removes the built-in badge, place the exact label outside the crop.
2. Put **Synthetic simulation** directly on slide 7's forecast chart. The forecast table is a simulator outcome, not a patient impact figure.
3. Put **BUILT PROTOTYPE** on current functions and **NOT BUILT — ROADMAP** on slide 11 and every future function in D6. A planned pilot is **PROPOSED PILOT**, not a deployed site.
4. Keep source and denominator near a number: “up to 16/20 sampled drugs at test-checked UP PHCs,” “1 in 3 baseline simulation runs,” and “12 synthetic TTS clips.”
5. Never use a stock icon or illustration as a substitute for a cited stockout result. Cite the [claims ledger](02-NUMBERS-AND-CLAIMS.md).

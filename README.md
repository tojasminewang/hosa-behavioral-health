# HOSA Behavioral Health study site (2026–27)

Live site: https://tojasminewang.github.io/hosa-behavioral-health/

A one-page study site for the HOSA Behavioral Health event: notes for every part of the test plan, 1,214 practice questions (normal and hard), 1,179 flashcards, a timed 50-question mock exam (60 or 40 minutes), highlights and personal notes. Progress is saved in your browser.

Notes are written from the event's official references (Cacioppo & Freberg, *Discovering Psychology*; the SAMHSA website; the NAMI website) plus the HOSA event guidelines and HOSA Canada study decks.

## Rebuilding

The page is generated from the files in `src/`:

- `src/notes/*.md` – the study notes (one file per topic)
- `src/questions/*.txt` – the quiz questions; every question points to the notes line it comes from
- `src/template.html` – the page design and app code
- `src/build.py` – checks the questions and writes `index.html`

```bash
python3 src/build.py --check   # check every question against the notes
python3 src/build.py           # rebuild index.html
```

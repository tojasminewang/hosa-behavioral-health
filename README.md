# HOSA Behavioral Health study site (2026–27)

Live site: https://tojasminewang.github.io/hosa-behavioral-health/

**For now, the site shows only HOSA Canada's Behavioural Health study slides**: the 11 decks in Modules 2–7, as reworded notes that cover all the facts on the slides (including their summary tables and pictures), with 50 diagrams and labeled pictures, 1,259 practice questions (normal and hard), 510 flashcards, a timed 50-question mock exam (60 or 40 minutes), highlights and personal notes. Each slide module matches one part of the test plan, so the decks fill the six parts and the mock exam keeps the test-plan weights. Progress is saved in your browser.

The full study notes are still in `src/`, left out of the page for now. They cover every part of the test plan and were written from the event's official references (Cacioppo & Freberg, *Discovering Psychology*; the SAMHSA website; the NAMI website) plus the HOSA event guidelines. They have 42 diagrams and labeled pictures, 1,214 practice questions and 1,179 flashcards. To put them back on the site, set `SLIDES_ONLY = False` in `src/build.py`, or build with `--full`.

The pictures in `img/` were made with AI (gpt-image) and contain no text; their labels, like every diagram, use only facts from the notes.

## Rebuilding

The page is generated from the files in `src/`:

- `src/notes/*.md` – the study notes (one file per topic)
- `src/questions/*.txt` – the quiz questions; every question points to the notes line it comes from
- `src/notes/hc-*.md` and `src/questions/hc-*.txt` – the HOSA slides; their decks are listed in `SLIDE_DECKS` in `src/build.py`
- `src/figures/*.html` – the diagrams and labeled pictures, placed in the notes with a line `![Caption](name)`
- `img/*.webp` – the pictures the figures show
- `src/template.html` – the page design and app code
- `src/build.py` – checks the questions and writes `index.html`

```bash
python3 src/build.py --check   # check every question against the notes (add --full for every topic)
python3 src/build.py           # rebuild index.html: the HOSA slides only, for now
python3 src/build.py --full    # rebuild index.html with every topic
```

# Post-lab reflection — template (T + 1 week, one page)

Required by the course: *"Revised final lab package plus a one-page reflection informed by
classmates' feedback."* Fill this in from evidence, not impressions.

## 1 · Evidence collected

| Metric | Target | Actual |
|---|---|---|
| Students with working setup on arrival | >85% | |
| Quiz: median score / 8 | 5–6 | |
| Quiz: worst-scoring question | — | |
| Task 1 finished within 5 min | >70% | |
| Task 3 finished within 8 min | >70% | |
| Reached Task 4a in session | >80% | |
| Autograder pass rate: Task 1 / 2 / 3 | >90 / >80 / >75% | |
| Submissions with a complete Task 4 matrix | >85% | |
| Extension attempted | >25% | |
| Ran over / under by | ±2 min | |

## 2 · The design bets — did they pay off?

For each, say **what you observed**, not what you hoped.

1. **"SQL as instrument, not subject."** Did the room engage with the *why*, or did they
   treat Tasks 1–3 as a syntax exercise and Task 4 as a demo to watch?
2. **Planting quiz Q3 and Q8, then resolving them in Tasks 3 and 4.** Did anyone refer back
   to the quiz unprompted? (F should have been listening for this.)
3. **Zero-install setup.** Did the `pip install duckdb` + one script path actually hold for
   every OS in the room?
4. **Bidirectional measurement.** Did it stop the "column stores are just faster"
   conclusion? Evidence: how many 4f answers gave an unconditional ranking?
5. **Task 4d (the optimiser mistake).** Was Week 1 too early for it, or was being able to
   *find* it the thing that made the lab feel advanced?

## 3 · What we got wrong

Be specific and name the fix. Things to look at honestly:

- Was 35 minutes right for 4 tasks, or should it have been 3 tasks?
- Did the handout's prose get read, or did students skip to the code blocks?
- Which questions did students ask that the handout should have pre-empted?
- Did the autograder's failure messages actually diagnose, or did students come to us anyway?
- Was giving SQLite an index and DuckDB none read as an unfair comparison by anyone? Did
  Task 4c's framing defuse it?

## 4 · Changes made to the final package

| # | Change | Driven by |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

## 5 · Handover to later teams

Teams 2, 3 and 6 inherit directly from this lab — Week 2 is storage and buffer management,
Week 3 is storage models and compression, Week 6 is cost estimation and plan search. Each
has a thread already pulled here:

- **Team 2 (storage, buffer management):** our sf=0.1 data fits entirely in page cache, so
  our lab is CPU-bound and shows no buffer-pool effects. Extension E4 documents this. A
  larger scale factor is where your lab begins.
- **Team 3 (storage models, compression):** Task 4e ends on "a covering index is a
  hand-built column projection." That is your opening.
- **Team 6 (cost estimation, plan search):** Task 4d is a live, reproducible
  cardinality-estimation failure in SQLite, with the plan and the fix. Reuse it — our data
  builder and `bench.py --explain` give it to you for free.

Also hand over: the prebuilt `data/` USB stick, and the Canvas setup-thread pattern. Both
saved us classroom time.

# COMP5330 Week 1 — Hands-on Lab, Part A: SQL

**Same SQL, two architectures.** A 35-minute lab for Week 1 (*DBMS architectures, OLTP vs.
OLAP, in-memory; SQL & RA*), to be followed by a 25-minute Relational Algebra half on the
same database. Designed and run by **Team 1**.

## The one-sentence idea

Students already know SQL, so SQL is not the subject — it is the **instrument**. They run
the *identical query text* on the *identical data* in a columnar engine (DuckDB) and a
row-oriented engine (SQLite) and measure **35–80× one way and 90–180× the other**, then
explain the difference from storage layout and execution model. Along the way they meet a
query that returns a silently wrong answer, and a real cost-based optimiser mistake.

## Why this design

A Week 1 lab on "SQL" in an *advanced* course risks being a COMP3030 rerun. Three choices
avoid that:

1. **SQL is the instrument, architecture is the subject.** Every task ends in a question
   about *why the system behaved that way*, which is CLO1.
2. **Two engines, not one.** The OLTP/OLAP split stops being a slide and becomes a number
   the student measured on their own laptop, in both directions — so nobody leaves thinking
   "column stores are just faster."
3. **Zero-server, zero-download.** Both engines are in-process; the dataset is *generated*
   locally. Setup is `pip install duckdb` plus one script. Nothing to install in the room,
   no classroom-wifi download, no Docker, identical on Windows, macOS and Linux.

## Contents

```
README.md                      this file
SETUP.md                       student-facing setup, 3 commands + troubleshooting
rubric.md                      how students' submissions are marked
handout/handout.md             THE STUDENT HANDOUT -- release at T-48h
quiz/quiz.md                   8 live questions + 2 spare, keys, debrief notes
setup/build_data.py            generates TPC-H in DuckDB, exports to SQLite
setup/verify_setup.py          student self-check, prints a fingerprint
starter/bench.py               Task 4 timing harness (median of 7, warm-up discarded)
answers/                       stubs students fill in and submit
solutions/*.sql                reference queries          -- FACILITATOR ONLY
solutions/SOLUTION-KEY.md      full key, measured numbers, common wrong answers, cut order
autograder/grade.py            property-based grader for Tasks 1-3
facilitation/run-of-show.md    minute-by-minute, roles, failure modes
facilitation/BRIDGE-TO-RA.md   interface contract with the Relational Algebra half
facilitation/reflection.md     T+1 week reflection template
```

## Quick start (facilitator)

```bash
pip install duckdb
```

```bash
python setup/build_data.py && python setup/verify_setup.py
```

```bash
python autograder/grade.py --solutions
```

The third command grades the reference solutions and must print **5/5 checks passed**. Run
it after any edit to the data builder — it is the package's regression test.

```bash
python starter/bench.py
```

## Reproducibility

- **Generated, not downloaded.** `build_data.py` calls DuckDB's `tpch` extension at
  `sf=0.1`; the extension is fetched once (~2 MB) on first run and cached. After that the
  build is offline.
- **Fixed seed.** The `held_order` table is built with `random.Random(5330)`, so every
  student has byte-identical data and the autograder's expected values are exact.
- **Verified.** `verify_setup.py` checks all 9 row counts, confirms the two engines return
  identical results for the reference query, and confirms the planted NULLs survived.
- **Cost:** ~170 MB on disk (30 MB DuckDB + 137 MB SQLite) and about **3 seconds** to
  build, plus a one-off few seconds on the very first run while the `tpch` extension
  downloads.
- Developed and measured against **DuckDB 2.0.0** and **SQLite 3.41.2** on Python 3.11.
  Nothing depends on a version-specific feature; `verify_setup.py` enforces SQLite ≥ 3.25.

## Mapping to the course

| Lab element | CLO | Week 1 topic |
|---|---|---|
| Task 4a–4c: measure and explain both directions | CLO1 | row vs column stores, OLTP vs OLAP |
| Task 4d: find the optimiser's cardinality error | CLO3 | previews Weeks 5–6 |
| Task 4e: covering index as a hand-built column store | CLO1, CLO2 | storage models, previews Week 3 |
| Task 3: three-valued logic breaks an anti-join | CLO3 | SQL semantics |
| Task 3(e): SQL is not relational algebra | CLO1 | hands off to Part B |
| Task 2: joins change aggregate grain | CLO3 | SQL semantics, bag vs set |
| Extension E4: in-memory is architecture, not caching | CLO1 | in-memory systems |
| Task 1 + quiz: the clause pipeline | CLO2 | SQL evaluation order |

Links to real systems, as required of the teach-back: **DuckDB** and **SQLite** are used
directly, and students read the output of both engines' `EXPLAIN`. The workload is
**TPC-H**, the standard decision-support benchmark.

## Prior art we drew on

- **DuckDB's own teaching tutorial** (Pedro Holanda, DuckDB core team) compares DuckDB,
  SQLite and Pandas on performance and usability, and has a second exercise on the query
  optimiser — the closest precedent for this lab's structure.
  <https://github.com/pdet/duckdb-tutorial>
- **CMU 15-445/645** (Andy Pavlo) HW1 ships a SQLite database and one `qN.sql` file per
  question, graded by comparing output — the file layout and grading model here follow it.
  <https://15445.courses.cs.cmu.edu>
- **UC Berkeley CS 186** project 1 fixes the view and column names as the grading
  interface; our autograder checks result *properties* for the same reason.
  <https://cs186.gitbook.io/project/assignments/proj1/your-tasks>
- **Edinburgh ADBS** lectures 02 (SQL) and 03 (Relational Algebra) are the course's primary
  materials; Task 1, the quiz's clause-pipeline and `HAVING` items, and the RA notation in
  the bridge note all follow them. <https://opencourse.inf.ed.ac.uk/adbs>
- **TPC-H** (TPC Benchmark™ H) for the schema and Query 1.

## What we would change with more time

- The point-lookup comparison gives SQLite an index and DuckDB none. That is the honest
  default for each architecture, and Task 4c makes students confront it directly rather
  than hiding it — but a fourth column measuring DuckDB *with* an ART index would make the
  argument airtight.
- `sf=0.1` fits in page cache on every modern laptop, so the lab is CPU-bound throughout and
  cannot show buffer-pool effects. That is deliberate (Week 2 owns storage and buffer
  management) and extension E4 turns the limitation into the exercise.

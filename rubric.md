# Marking rubric — Week 1 Lab, Part A (SQL)

This is the **students'** rubric for their lab submission. It is distributed with the
handout. *(The team's own mark for designing and running the lab is the separate 25% "Lab
Design" component in the course rubric.)*

**Weight:** Part A counts toward the 10% Participation component, pro-rated across the
semester's labs. Tasks 1–3 are near-binary; Task 4 and the extension are where marks
separate.

**Due Sunday 15 Nov 23:59** on Canvas or your lab repo.

| # | Item | Pts | How it is marked |
|---|---|----:|---|
| 1 | `q1.sql` | 8 | Autograded. 4 rows, 6 columns, exact aggregates. |
| 2 | Q1.1 + Q1.2 written | 4 | `WHERE` vs `HAVING` reasoning (2); why both engines *must* agree (2). |
| 3 | `q2.sql` | 10 | Autograded. 10 rows, correct top-3 keys, deterministic order. |
| 4 | Q2.1–Q2.3 written | 8 | `GROUP BY` rule (2); why the tie-break (2); the ≈4× grain explanation **with the general rule stated** (4). |
| 5 | Task 3 (a)+(b) | 8 | Reports 0; gives the three-valued-logic argument, naming `UNKNOWN` and what `WHERE` admits. |
| 6 | Task 3 (c) — three repairs | 12 | Autograded, 4 each. All three must return 149,960. |
| 7 | Task 3 (d) | 6 | Full marks require **robust by construction vs by vigilance**. "It's faster" alone: 2/6. |
| 8 | Task 3 (e) | 4 | SQL is not RA; the algebra has no NULL, so this failure is inexpressible. |
| 9 | Task 4a — the matrix | 8 | All 10 cells filled, with the *Guess* column completed. Marked for completeness, **not** for predicting correctly. |
| 10 | Task 4b — scan direction | 10 | Both mechanisms, bytes-read **and** work-per-value (6). The S3-vs-S1 quantitative check (4) — this is the discriminator. |
| 11 | Task 4c — point direction | 8 | B-tree descent + row locality (4); and a defensible answer on whether the missing index is an oversight or a design choice (4). |
| 12 | Task 4d — the optimiser mistake | 10 | Identifies the plan line (3); explains random vs sequential access at 98.5% selectivity (4); reports the recovered factor (3). |
| 13 | Task 4e — covering index | 8 | Resolves the contradiction via *which columns* (4); "a covering index is a hand-built column projection" (4). |
| 14 | Task 4f — conclusion ¶ | 6 | A workload-shaped criterion, citing your own numbers. Product preference with no criterion: 0. |
| | **Subtotal** | **110** | |
| 15 | Extension E1–E4 | +15 | Optional. Measurements **and** a mechanism. A clean negative result, correctly interpreted, scores full marks. |
| | **Total** | **125** | Scaled to the participation weight. |

## What distinguishes the top band

| Band | Looks like |
|---|---|
| **Excellent (85–100%)** | Explanations name *mechanisms* and test them against the measurements. Uses the data to **choose between** two candidate explanations rather than asserting both. Reports ratios, not milliseconds. Notices at least one thing the handout did not ask about. |
| **Good (70–84%)** | All tasks correct; explanations name the right mechanisms but do not check them against the numbers. |
| **Satisfactory (55–69%)** | Queries correct; prose restates the handout's vocabulary without adding reasoning. |
| **Weak (<55%)** | Queries correct but prose absent or purely descriptive ("DuckDB was faster"). Or Task 3 repairs that pass without any account of *why* `NOT IN` failed. |

## Specific things that lose marks

- **Quoting milliseconds as if they were facts about the engines.** Your laptop is not a
  benchmark platform. Ratios and mechanisms.
- **Asserting both mechanisms in 4b without checking which one the S3-vs-S1 data supports.**
  The check is the point of the task.
- **"DuckDB is faster than SQLite."** You measured a case where SQLite is ~180× faster.
  Any unconditional ranking is wrong.
- **Hardcoding expected values.** The autograder rejects literal `149960` in your SQL.
- **A Task 3 repair that works only on today's data.** `WHERE h.ho_reason IS NULL` is the
  planted near-miss; it returns 149,961.

## Things that gain marks

- Finding and reporting a **disagreement with our reference numbers**, with a hypothesis
  about why (different core count, battery/power profile, cold cache, DuckDB version).
- A **negative result honestly interpreted** — especially extension E4, where "no
  significant change, because sf=0.1 already fits in page cache, so this workload is
  CPU-bound" is the *correct* finding and earns full marks.
- Spotting that `orders` has 10,000 distinct customers while `customer` has 15,000 rows,
  and saying what the inner join in Task 2 silently did about it.
- Any question we cannot answer on the spot. Please write those down — they go into the
  team's post-lab reflection.

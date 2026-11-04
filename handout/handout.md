# COMP5330 · Week 1 Lab — Part A: SQL
### *Same SQL, two architectures*

**Fri 13 Nov 2026 · Room D302 · 16:30–17:30 · Part A (SQL) 35 min · Part B (Relational Algebra) 25 min**
**Run by Team 1.** Part A is this handout. Part B follows immediately, on the same database.

---

## Why this lab is not a SQL tutorial

You already wrote SQL in COMP3030. This lab uses SQL as an **instrument** for the question
this week's lecture opened: *why does the same declarative query behave completely
differently on two different DBMS architectures?*

You will run the **identical SQL text** against two engines holding the **identical data**:

| | DuckDB | SQLite |
|---|---|---|
| Storage layout | **columnar** (values of one column stored together) | **row-oriented** (whole tuples stored together) |
| Execution model | **vectorised** — operators process batches of ~2048 values | **tuple-at-a-time** — one row pulled through the operator tree |
| Secondary indexes | none in this lab (relies on per-row-group min/max **zone maps**) | B-tree indexes on every primary key (**we created them for you**) |
| Designed for | **OLAP** — scan many rows, few columns, aggregate | **OLTP** — find few rows, touch all their columns |

Both are **in-process** (no server), which is exactly why we can run both on your laptop
and why the comparison is apples-to-apples: same machine, same cache, same data.

### Learning objectives

By the end of Part A you can:

1. **(CLO1)** Predict, measure and *explain* which of a row store and a column store wins a
   given query, in terms of bytes read and work per tuple.
2. **(CLO1, CLO3)** Read a physical query plan and name the operators the optimiser chose.
3. **(CLO3)** Diagnose a query that returns a **silently wrong answer** because of SQL's
   three-valued logic, and repair it three different ways.
4. **(CLO3)** Recognise a cost-based **optimiser mistake** from a plan and overrule it.
5. **(CLO2)** State what "declarative" buys you and what it costs you.

---

## 0 · Before you arrive (do this at home — it needs ~2 minutes of network)

```bash
pip install duckdb
```

```bash
python setup/build_data.py
```

```bash
python setup/verify_setup.py
```

`build_data.py` **generates** TPC-H at scale factor 0.1 locally with DuckDB's `tpch`
extension and exports the same rows into SQLite — nothing large is downloaded, and the
result is identical on every machine. Expect **a few seconds** and **~170 MB** on disk
(the first run also spends a moment downloading the `tpch` extension).

`verify_setup.py` prints a fingerprint line. **Paste it into the Canvas thread
"Week 1 lab — setup check" before Friday.** If it fails it tells you exactly what to fix.

> **If you arrive without this done**, sit next to someone who did. You will still be able
> to do Tasks 1–3; Task 4 needs the data on your own machine.

### The database

TPC-H, the standard decision-support benchmark: 8 tables, `lineitem` is the big one at
**600,572 rows**.

```
region(r_regionkey, r_name, …)                  5 rows
nation(n_nationkey, n_name, n_regionkey, …)    25
supplier(s_suppkey, s_name, s_nationkey, s_acctbal, …)      1,000
customer(c_custkey, c_name, c_nationkey, c_acctbal, c_mktsegment, …)   15,000
part(p_partkey, p_name, p_brand, p_type, p_size, p_retailprice, …)     20,000
partsupp(ps_partkey, ps_suppkey, ps_availqty, ps_supplycost, …)        80,000
orders(o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, …)  150,000
lineitem(l_orderkey, l_linenumber, l_quantity, l_extendedprice,
         l_discount, l_tax, l_returnflag, l_linestatus, l_shipdate, …)    600,572
```

Plus one table we added, which is **deliberately dirty — do not clean it**:

```
held_order(ho_orderkey, ho_reason)   42 rows
```

> *Story:* orders flagged by the fraud-review system. A buggy ETL job wrote some rows
> with no order key. Task 3 is about what that does to your query.

### How to run SQL

```bash
python -c "import duckdb; duckdb.connect('data/tpch.duckdb').sql(open('answers/q1.sql').read()).show()"
```

Or interactively — pick whichever you prefer:

```bash
python -i -c "import duckdb; d=duckdb.connect('data/tpch.duckdb'); import sqlite3; s=sqlite3.connect('data/tpch.sqlite')"
```

Write each answer into `answers/qN.sql` (one statement, no trailing semicolon needed), then:

```bash
python autograder/grade.py
```

---

## Task 1 · The clause pipeline  · 5 min · `answers/q1.sql`

> **Write one query.** For every `(l_returnflag, l_linestatus)` pair, over line items with
> `l_shipdate <= '1998-09-01'`, report:
>
> `l_returnflag`, `l_linestatus`, the number of line items as `cnt`, `SUM(l_quantity)` as
> `sum_qty`, `SUM(l_extendedprice)` as `sum_price`, and `AVG(l_discount)` as `avg_disc`.
>
> Order by `l_returnflag`, then `l_linestatus`.

This is TPC-H Query 1, the most-quoted analytics query in the field. You get 4 rows.

**Q1.1** You could have written the date restriction in `WHERE` or in `HAVING`. One of them
is wrong and one is merely wasteful. Which is which, and why? Answer in one sentence.

**Q1.2** Run it in **both** engines and confirm the numbers are identical. They must be —
*why* must they be? (This is the contract from quiz Q7.)

> **Checkpoint — raise a hand when your 4 rows match your neighbour's.** The first row is
> `A | F | 147790 | …`.

---

## Task 2 · Joins change the grain  · 7 min · `answers/q2.sql`

> **Write one query.** For each customer who has placed **more than 15 orders**, report
> `c_custkey`, `c_name`, the customer's nation name as `n_name`, the number of their orders
> as `n_orders`, and the total value of those orders as `total_value`.
>
> Return only the **10 highest `total_value`**, breaking ties by `c_custkey` ascending.

Three tables: `customer`, `nation`, `orders`.

**Q2.1** Your `SELECT` lists `c_custkey`, `c_name` and `n_name` without aggregating them.
What must your `GROUP BY` contain, and why is grouping by `c_custkey` alone not enough for
the standard even though `c_name` is functionally determined by it?

**Q2.2** Why does the task insist on the `c_custkey` tie-break? Give the precise failure it
prevents. (Quiz Q5.)

**Q2.3 — the trap.** Now add `lineitem` to your `FROM` with
`JOIN lineitem l ON l.l_orderkey = o.o_orderkey`, changing nothing else. `n_orders` and
`total_value` both change. **Explain the exact factor by which `total_value` grows** and
state the general rule about joins and aggregate grain. Then fix it while keeping
`lineitem` in the query. *(Hint: aggregate at one grain before joining to the other.)*

> **This is the single most common silent bug in production reporting SQL.** If your team
> only remembers one thing from Part A, this is a good candidate.

---

## Task 3 · A query that lies to you  · 8 min · `answers/q3.sql`

Run this **exactly as given**:

```sql
SELECT COUNT(*) AS not_held
  FROM orders o
 WHERE o.o_orderkey NOT IN (SELECT ho_orderkey FROM held_order);
```

`orders` has 150,000 rows. `held_order` holds 40 real order keys. You expect **149,960**.

**(a) What do you actually get?** Run it in both engines. Note that they agree — this is
not a bug in either engine; it is what the SQL standard requires.

**(b) Diagnose it.** Write a query against `held_order` that demonstrates the cause in one
result. Then write the Boolean-logic argument in one or two sentences:
what is the truth value of `150 <> NULL`, and what does `WHERE` do with it?

**(c) Repair it three ways** and confirm all three return 149,960:

| | approach |
|---|---|
| **i** | `NOT EXISTS` with a correlated subquery |
| **ii** | `LEFT JOIN` … `WHERE … IS NULL` (an *anti-join*) |
| **iii** | keep `NOT IN`, but make the subquery NULL-free |

Put **(iii)** in `answers/q3.sql`. Keep (i) and (ii) — the grader checks all three.

**(d) Which repair would you ship, and why?** Consider: what happens to each of the three
if tomorrow's ETL writes a *third* NULL row? Which one is robust *by construction* rather
than by remembering to filter?

**(e) Bridge to Part B.** Relational algebra has no NULL and no three-valued logic: the
anti-join is just set difference, `orders − held_order`. So this failure mode **cannot be
expressed** in the algebra you are about to study. What does that tell you about the
relationship between SQL and the relational model? *(One sentence. Hold your answer — the
RA half will come back to it.)*

---

## Task 4 · Same SQL, two architectures  · 12 min · `answers/task4.md`

Now the measurement. **Predict before you run** — write your predictions in the table's
*Guess* column first; you will not be marked on accuracy, only on having committed.

```bash
python starter/bench.py
```

The harness opens one connection per engine, discards a warm-up run, times 7 repetitions
and reports the **median**. Read the method in `starter/bench.py` before trusting it — and
say what you think of it in (d).

### 4a · Fill this in

| Query | what it touches | Guess: who wins? | DuckDB (ms) | SQLite (ms) | Speed-up | Winner |
|---|---|---|---|---|---|---|
| `S1-scan-agg` | 600k rows, 5 of 16 cols, GROUP BY | | | | | |
| `S2-scan-agg-filtered` | same + `l_shipdate` predicate | | | | | |
| `S3-one-column` | 600k rows, **1** of 16 cols | | | | | |
| `P1-point-order` | **1 row** of `orders`, all cols | | | | | |
| `P2-point-customer` | **1 row** of `customer`, 2 cols | | | | | |

### 4b · Explain the scan direction (S1, S3)

One engine wins these by a wide margin. Give **two independent reasons**, one about
**bytes read** and one about **work per value**. Then use S3 vs S1 to support the
bytes-read argument quantitatively: S3 needs 1 column, S1 needs 5 — does the ratio move in
the direction your argument predicts? What does that tell you about *projection pushdown*?

### 4c · Explain the point direction (P1, P2)

The other engine wins these, and by a larger factor than you probably guessed. Why can a
B-tree index descent beat *any* amount of vectorised scanning here? And since we gave
SQLite its indexes but gave DuckDB none, answer the fair question: **would adding an index
to DuckDB close the gap, and is the absence of one an oversight or a design choice for an
OLAP engine?** *(Hint: look up what DuckDB stores per row group instead.)*

### 4d · The anomaly — find the optimiser's mistake

`S2` is `S1` plus a `WHERE` clause. It does strictly **less** work. Yet in SQLite, `S2` is
about **3× slower** than `S1`.

1. Get the plan for both:
   ```bash
   python starter/bench.py --explain
   ```
   In SQLite, look for the line containing `SEARCH` or `SCAN` on `lineitem`.
2. The predicate `l_shipdate <= '1998-09-01'` matches **591,673 of 600,572 rows (98.5%)**.
   SQLite chose to use `idx_lineitem_ship`. **Explain why that choice is catastrophic**
   for a predicate this unselective. Think about what the engine must do *per matching row*
   once it has the index entry.
3. Overrule it. SQLite accepts a hint:
   ```sql
   ... FROM lineitem NOT INDEXED WHERE l_shipdate <= '1998-09-01' ...
   ```
   Re-measure:
   ```bash
   python starter/bench.py --sql "PASTE YOUR NOT-INDEXED QUERY HERE"
   ```
   Report the new time and the factor you recovered.
4. DuckDB's time barely changes between S1 and S2. Connect that to the table at the top of
   this handout: **what did DuckDB not have the opportunity to get wrong?**

> This is a genuine, reproducible **cardinality-estimation failure** — the optimiser
> believed the predicate was selective. Weeks 5 and 6 are about exactly this. You found it
> in Week 1.

### 4e · The question that explains why column stores exist

In SQLite, these two run at very different speeds:

```sql
SELECT COUNT(*) FROM lineitem WHERE l_shipdate <= '1998-09-01';   -- uses the index
SELECT COUNT(*) FROM lineitem NOT INDEXED WHERE l_shipdate <= '1998-09-01';
```

The indexed one is **faster** here (~3×), while in 4d the *same index* made things ~3×
slower. Resolve the apparent contradiction in terms of which **columns** each query needs.

> **Look closely at the two plans.** SQLite tells you the answer in one word:
> ```
> 4d (S2):  SEARCH lineitem USING INDEX idx_lineitem_ship (l_shipdate<?)
> 4e:       SEARCH lineitem USING COVERING INDEX idx_lineitem_ship (l_shipdate<?)
> ```
> Find that word, and say what the engine must do in the first case that it skips in the
> second. That one difference is worth ~60× on this data.

Then the payoff: a B-tree index on `(l_shipdate)` that answers a query *without touching
the table* is called an **index-only scan**. Describe, in one or two sentences, in what
sense a covering index is a row store **imitating** a column store — and what a column
store therefore gives you that you would otherwise have to build one index at a time.

### 4f · Record your conclusion

In `answers/task4.md`, write **one paragraph (≤150 words)** completing this sentence with
your own measurements as evidence:

> *"Given a workload, I would choose a row store over a column store when …, because …"*

---

## Extension challenge · open-ended · take-home, due with the lab reflection

Pick **one**. Submit measurements plus ≤400 words in `answers/extension.md`.

**E1 · Make each engine win by a landslide.** Construct a query where SQLite beats DuckDB
by **>10×**, and another where DuckDB beats SQLite by **>50×**, on this same unmodified
database. Then rebuild at 10× the data:
```bash
python setup/build_data.py --sf 1 --outdir data
```
Report how each ratio changes with scale and **explain which way each should move and why**.
A ratio that stays flat is as interesting as one that grows — say which you got.

**E2 · Build a column store inside SQLite.** Create a covering index that makes `S1`
dramatically faster in SQLite, measure it, and report how close you get to DuckDB. Then
explain the two things you *cannot* get this way no matter how many indexes you add.
*(Think: compression, and what happens to your write throughput.)*

**E3 · Break the optimiser on purpose.** Find a *second* query where SQLite's planner makes
a cost-estimation mistake that costs ≥2×. Show the plan, the fix, and state the
estimation error in terms of the true vs. assumed selectivity. Then run `ANALYZE` and
report whether fresh statistics change its mind.

**E4 · In-memory vs on-disk.** The lecture claimed in-memory systems are a distinct
architecture, not just "a bigger cache". Test it: copy each database into a RAM-backed
location (or use DuckDB's `:memory:` after `IMPORT`), repeat the Task 4 matrix, and report
which ratios change and which do not. Argue from your numbers whether this workload is
**I/O-bound or CPU-bound**, and what that implies about when in-memory architecture
actually pays.

---

## Submission

Push to your lab repo, or upload to Canvas, by **Sunday 15 Nov 23:59**:

```
answers/q1.sql  q2.sql  q3.sql        -- graded by autograder/grade.py
answers/q3_notexists.sql  q3_antijoin.sql
answers/task4.md                       -- the filled table + 4b–4f
answers/extension.md                   -- if you attempt one
```

Run the grader before you submit; it checks the same way we do:

```bash
python autograder/grade.py
```

**Marks within the lab** (this is participation + the lab's own rubric; see `rubric.md`):
Tasks 1–3 are checked mechanically and are near-binary. Task 4's prose and the extension
are where the marks separate — we are grading the **explanation**, not the milliseconds.

---

## A note on the timings you will report

Your absolute numbers will differ from ours and from each other's — different CPUs, caches
and background load. **Report ratios and reason about mechanisms.** A lab report that says
"DuckDB took 4.1 ms" is weaker than one that says "DuckDB won S3 by ~40× and S1 by ~35×,
and the gap narrows as the query touches more columns, consistent with projection pushdown
being the dominant effect." The second sentence is the skill this course is teaching.

# Week 1 Lab — Concept-check quiz (SQL half)

**Format.** 8 scored questions, 45 s each, run live (Menti / Kahoot / Google Form).
Budget **8 minutes total**: ~6 min answering, ~2 min debrief on the two questions the
class got worst. Two spare questions at the end if you finish early or need a tie-break.

**Design rule we followed.** Every distractor is a *real misconception*, not a plausible-looking
wrong string. A student who has memorised syntax but not semantics should score ~50%.
The debrief note under each question is the actual teaching moment — it matters more than
the score. **Do not skip the debrief to save time; cut a question instead.**

**Not graded for marks.** Announce this. It is a diagnostic: it tells you which tasks to
slow down on, and it plants Q3 and Q8, which Tasks 3 and 4 then resolve.

---

## Q1 · Where does a clause live?

```sql
SELECT dept, AVG(age) AS avg_age
  FROM Student
 WHERE avg_age > 21
 GROUP BY dept
```

**What happens?**

- A. Returns departments whose average age exceeds 21
- B. Returns nothing, because no department qualifies
- C. **Error: `avg_age` cannot be referenced in `WHERE`** ✅
- D. Works, but the result is non-deterministic

> **Debrief.** `WHERE` is evaluated *before* grouping and aggregation, so at that point
> neither the group nor `avg_age` exists yet. The fix is `HAVING AVG(age) > 21`.
> Walk the class back through the conceptual order:
> `FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`.
> The `SELECT` alias is created in step 5 — that is *why* steps 2 cannot see it.
> This is the red-X slide from the lecture; it is question 1 because it is the single
> most common SQL error in this class.

---

## Q2 · `COUNT(*)` vs `COUNT(column)`

`Enrolled` has 10 rows. In 3 of them, `grade` is `NULL`. The 7 non-null grades sum to 490.

What does this return?

```sql
SELECT COUNT(*), COUNT(grade), AVG(grade) FROM Enrolled
```

- A. 10, 10, 49
- B. 10, 7, 49
- C. **10, 7, 70** ✅
- D. 7, 7, 70

> **Debrief.** Three separate rules in one line:
> `COUNT(*)` counts **rows** (10). `COUNT(expr)` counts **non-NULL values** (7).
> And every aggregate except `COUNT(*)` **silently skips NULLs**, so `AVG(grade)` is
> 490/**7** = 70, not 490/10 = 49.
> Option B is the trap worth naming: it assumes `AVG` divides by the row count, i.e. that
> a NULL counts as a 0. It does not. A NULL is "no value", not "zero".
> Make the modelling point explicit: if those 3 students genuinely scored nothing, then 49
> is the number you wanted and SQL just quietly gave you 70. The aggregate made a
> modelling decision on your behalf. `AVG(COALESCE(grade, 0))` is how you take it back.

## Q3 · The anti-join that returns nothing

`held_order` contains 40 real order keys **and 2 rows where `ho_orderkey IS NULL`**.
`orders` has 150,000 rows.

```sql
SELECT COUNT(*) FROM orders
 WHERE o_orderkey NOT IN (SELECT ho_orderkey FROM held_order)
```

- A. 149,960
- B. 149,998
- C. 150,000
- D. **0** ✅

> **Debrief.** `x NOT IN (S)` is `x <> s1 AND x <> s2 AND …`. One comparison against NULL
> yields `UNKNOWN`, and `TRUE AND UNKNOWN = UNKNOWN`, which `WHERE` does not pass. So
> *every* row is filtered out. Say the consequence out loud: **this is a silent wrong
> answer, not an error** — the scariest failure mode a query has.
> Don't give the fix yet: **Task 3 is this exact query.** Tell them they'll meet it again
> in ten minutes.

---

## Q4 · Outer join, then filter

```sql
SELECT c.c_name, o.o_totalprice
  FROM customer c LEFT JOIN orders o ON o.o_custkey = c.c_custkey
 WHERE o.o_totalprice > 1000
```

5,000 of our 15,000 customers have placed no orders. How many of those 5,000 appear in
the result?

- A. All 5,000, with `NULL` in `o_totalprice`
- B. **None — the `WHERE` turns the outer join back into an inner join** ✅
- C. All 5,000, with `0` in `o_totalprice`
- D. Error: cannot filter a nullable column

> **Debrief.** The join manufactures `o_totalprice = NULL` for the unmatched customers;
> then `NULL > 1000` is `UNKNOWN` and the row is dropped. The outer join did its job and
> the `WHERE` undid it. If you want the condition to apply only to matched rows, it belongs
> in `ON`; if you want to keep the unmatched ones, you need
> `WHERE o.o_totalprice > 1000 OR o.o_orderkey IS NULL`.
> **`ON` filters before the join is completed; `WHERE` filters after.**

---

## Q5 · `LIMIT` without `ORDER BY`

```sql
SELECT c_name FROM customer LIMIT 5
```

Run twice on the same unchanged database, possibly on two different DBMSs.

- A. Always the same 5 names, in the same order
- B. Always the same 5 names, possibly reordered
- C. **Any 5 names — the result is not determined by the query** ✅
- D. An error: `LIMIT` requires `ORDER BY`

> **Debrief.** A relation is an unordered bag. With no `ORDER BY`, *which* 5 rows you get
> is an artefact of the physical plan — scan order, parallelism, which row group came back
> first. Same query, same data, different answer. In DuckDB it can even change between runs
> because the scan is parallel. The rule: **`LIMIT` without `ORDER BY` is a bug**, and
> `ORDER BY` on a non-unique key is only *half* a fix — you need a tie-breaker to make it
> total (that's why Task 2 asks for `ORDER BY total_value DESC, c_custkey ASC`).

---

## Q6 · What a join does to an aggregate

Customer 42 has 3 orders. Each of those orders has 4 line items.

```sql
SELECT SUM(o.o_totalprice)
  FROM orders o JOIN lineitem l ON l.l_orderkey = o.o_orderkey
 WHERE o.o_custkey = 42
```

- A. The correct total of the 3 orders
- B. **4× the correct total** ✅
- C. 3× the correct total
- D. 12× the correct total

> **Debrief.** The join replicates each order row once per matching line item, and `SUM`
> faithfully adds every copy. SQL is a **bag (multiset)** algebra — duplicates are data,
> and aggregates respect them. This is the most common *silent* reporting bug in industry.
> Note that `SELECT DISTINCT` would not save you either: the duplicated rows are identical,
> so there is nothing for `DISTINCT` to remove, and anyway `DISTINCT` is applied after the
> aggregate. The fix is to aggregate before joining (a subquery per grain), or
> `SUM(DISTINCT …)` only if the values happen to be unique, which is a trap of its own.
> **Flag this for the RA half:** pure relational algebra has *set* semantics and would not
> behave this way — that mismatch is exactly why real systems use bag semantics.

---

## Q7 · What "declarative" guarantees

The optimiser can execute a join as a nested-loop join, a hash join or a sort-merge join,
and can reorder the inputs. Which statement is true?

- A. Faster plans may return fewer rows, so you should pin the plan in production
- B. **Every plan the optimiser considers must return the same answer; it may only differ
  in time and memory** ✅
- C. The plan affects the answer only when the query contains aggregates
- D. The plan affects row *order* only when `ORDER BY` is absent, and nothing else

> **Debrief.** This is the contract that makes SQL worth having: the optimiser searches a
> space of *semantically equivalent* plans. D is seductive and nearly right — plan choice
> *does* affect unordered output order — but it is incomplete, which is the point: the
> guarantee is about the result *as a bag*, not about row order. Tie it forward: Weeks 5–6
> are entirely about how the system searches that space and how it estimates which plan is
> cheapest. Tie it sideways: in Task 4 you will see the *same* SQL produce a 35× time
> difference across two engines with identical answers.

---

## Q8 · Which workload wants a column store?

Same data, same SQL, two engines: one row-oriented with B-tree indexes, one columnar and
vectorised. Which query do you expect the **columnar** engine to win by the widest margin?

- A. `SELECT * FROM orders WHERE o_orderkey = 300001`
- B. `UPDATE customer SET c_acctbal = c_acctbal - 10 WHERE c_custkey = 9001`
- C. **`SELECT SUM(l_extendedprice) FROM lineitem`  (600k rows, 1 of 16 columns)** ✅
- D. `INSERT INTO orders VALUES (…)` — one new order

> **Debrief.** C touches **one column of many, over every row** — the column store reads
> ~1/16 of the bytes, decodes them in compressed batches and runs the aggregate over
> vectors rather than per tuple. A, B and D touch **one row, all columns**, which is
> precisely what a row store plus a B-tree is built for: one index descent, one page, done.
> This is the OLAP/OLTP split restated as a storage-layout question, and it is the
> hypothesis you will measure in Task 4. Ask for a prediction of the *magnitude* before the
> break — hold them to it afterwards.

---

## Spare Q9 · Non-aggregated columns

```sql
SELECT dept, name, AVG(age) FROM Student GROUP BY dept
```

- A. Returns one row per department, with an arbitrary `name`
- B. **Rejected by the standard: `name` is neither grouped nor aggregated** ✅
- C. Returns one row per (dept, name) pair
- D. Returns one row per department, with `name` set to `NULL`

> **Debrief.** A is what MySQL historically did and SQLite still permits — which is worse
> than an error, because it silently invents an answer. The standard requires every
> non-aggregated `SELECT` column to be functionally determined by the grouping columns.
> Good question for discussing *why* permissive engines cause production bugs. (Try it in
> SQLite during the lab and watch it succeed — then try it in DuckDB and watch it fail.)

---

## Spare Q10 · `DISTINCT` vs `GROUP BY`

Are these always equivalent?

```sql
SELECT DISTINCT dept FROM Student;
SELECT dept FROM Student GROUP BY dept;
```

- A. **Yes for this pair, but they diverge as soon as you add an aggregate or `HAVING`** ✅
- B. No, `DISTINCT` keeps NULLs and `GROUP BY` drops them
- C. No, `GROUP BY` sorts the output and `DISTINCT` does not
- D. Yes, always — `DISTINCT` is defined as `GROUP BY` on the select list

> **Debrief.** Both produce the distinct `dept` values, NULL included as a single group.
> C is a common myth: `GROUP BY` implies no ordering guarantee (many systems happen to sort
> when they use a sort-based grouping operator, which is a plan artefact — see Q5).
> `GROUP BY` is strictly more general: it also establishes the groups that aggregates and
> `HAVING` are computed over.

---

## Answer key (facilitator copy)

| Q | Key | Targets this misconception | If >40% miss it |
|---|-----|---------------------------|-----------------|
| 1 | C | `WHERE` can see `SELECT` aliases / can filter aggregates | Re-draw the clause pipeline before Task 1 |
| 2 | C | NULL behaves like 0 in aggregates (B is the `/10` trap) | Slow down; it reappears in Task 3 |
| 3 | D | `NOT IN` is safe with NULLs | Good — Task 3 is built to resolve this |
| 4 | B | An outer join survives any `WHERE` | Spend 60 s on `ON` vs `WHERE` |
| 5 | C | Tables have an inherent row order | Point at the tie-break in Task 2 |
| 6 | B | Joins don't change aggregate grain | Warn before Task 2; it is the trap there |
| 7 | B | Plan choice can change the answer | Core to the whole course — fix it now |
| 8 | C | Column stores are "just faster" | Good — Task 4 measures it |
| 9 | B | Permissive engines are standard | Optional |
| 10 | A | `GROUP BY` sorts / handles NULL differently | Optional |

**Live-run tip.** Show the per-question result bar *before* you reveal the key, and ask one
student who picked the most popular wrong answer to say why. Their reasoning is the
misconception in the room, and naming it is worth more than your explanation.

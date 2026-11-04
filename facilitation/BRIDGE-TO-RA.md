# Interface contract: SQL half → Relational Algebra half

**For whoever runs Part B.** Part A (SQL, 35 min) hands you the room at **17:05** with
25 minutes left. This note is the contract between the two halves so the hour reads as one
lab and not two.

## What you inherit for free

- **The same database, already on every laptop.** `data/tpch.duckdb` and
  `data/tpch.sqlite`. **No new setup, no new install.** Do not introduce a second dataset —
  the shared schema is what makes the two halves feel like one lab.
- **A room that has just seen query plans.** In Task 4 they read DuckDB `EXPLAIN` output and
  SQLite `EXPLAIN QUERY PLAN` output. They have seen the operator names but have **no
  formalism** for them. You are the formalism.
- **A live cliffhanger** (see below).

## The three hooks Part A deliberately leaves open

**1 · Task 3(e) — the cliffhanger. Open on this.**
Students found that

```sql
SELECT COUNT(*) FROM orders WHERE o_orderkey NOT IN (SELECT ho_orderkey FROM held_order)
```

returns **0** instead of 149,960, because `held_order` contains two NULL keys and
`x <> NULL` is UNKNOWN. Part A asked them "what does that tell you about SQL and the
relational model?" **and refused to answer it.** They are holding an answer.

Your opening: the algebra's anti-join is **set difference**, `orders − held_order`. It is
total, it has no NULL, no three-valued logic, and **this failure mode cannot be written
down in it.** SQL extends the relational model with NULLs for pragmatic reasons and in
doing so loses equivalences the algebra guarantees. That is a 90-second opening that lands
because they felt the bug ten minutes ago.

**2 · Bag vs. set semantics — already demonstrated, not yet named.**
Quiz Q6 and Task 2 Q2.3 both hit it: joining `lineitem` to `orders` replicated order rows
and inflated `SUM(o_totalprice)` by ≈4×. They have **experienced** bag semantics. Edinburgh
ADBS lecture 03 slide 7 makes the distinction formally (pure RA = set semantics; SQL =
multiset), and slide 9 explains why real systems do not auto-deduplicate projections
(aggregates need the duplicates; dedup is not free). You can cite their own 4× number as
the motivation.

**3 · Plans are algebra expressions — they have seen the plans.**
This is your strongest asset. In Task 4 they ran:

```bash
python starter/bench.py --explain
```

and saw real physical operators. Map them onto the algebra explicitly:

| What they saw in `EXPLAIN` | Algebra | Edinburgh notation |
|---|---|---|
| `PROJECTION` | projection | π |
| `FILTER`, `SEARCH … (l_shipdate<?)` | selection | σ |
| `HASH_JOIN`, `SEARCH … USING INDEX` | join (compound: σ over ×) | ⋈ |
| `HASH_GROUP_BY`, `USE TEMP B-TREE FOR GROUP BY` | grouping / aggregation | γ |
| `ORDER_BY` | sorting | τ |
| `DISTINCT` | duplicate elimination | δ |
| `SEQ_SCAN`, `SCAN lineitem` | the base relation | *R* |

Then ADBS lecture 03 slide 2 in reverse: **take Task 1's query and have them write it as an
algebra tree**, and compare their tree with the plan DuckDB actually printed. The point to
land: *the optimiser rewrote their tree, and Codd's theorem is why it is allowed to.*

## Notation — please use Edinburgh's, so the two halves match

From ADBS lecture 03: basic operators **σ π ⍴ ∪ −  ×**, compound **∩ ⋈**, extras
**γ** (group-by/aggregation), **δ** (duplicate elimination), **τ** (sort), **÷** (division).
Part A's handout and solution key use exactly these symbols in the bridge sections.

## Suggested shape for your 25 minutes

| Min | What |
|---|---|
| 2 | Resolve the Task 3(e) cliffhanger: anti-join = set difference, no NULLs in the algebra |
| 3 | The six basic operators on `region`/`nation` (5 and 25 rows — small enough to evaluate by hand on paper) |
| 5 | Set vs bag, using their own 4× inflation from Task 2 Q2.3 |
| 7 | **Hands on:** translate Task 1 and Task 2 into algebra trees; translate one algebra expression back into SQL and run it |
| 5 | Compare their tree against `EXPLAIN` output; name every operator |
| 3 | Codd's theorem, and why "the optimiser may rewrite your tree" is the same claim as Task 4's 35× |

## Two things to avoid

- **Do not re-teach joins.** Part A spent 7 minutes on joins and grain. Assume it.
- **Do not introduce a toy `Student`/`Enrolled` schema.** The lecture used it, but the lab
  has one database on 40 laptops and switching schemas mid-hour breaks the continuity that
  makes this feel like one lab. `region` (5 rows) and `nation` (25 rows) are small enough
  to evaluate any algebra expression by hand, and they are already loaded.

## What you should hand back at 17:30

One closing sentence that ties the hour together. Something like:

> "Part A measured a 35× difference between two engines running the same SQL. Part B showed
> you the language that difference is expressed in: both engines compiled your query into
> the same algebra, then picked different implementations of the same operators. Weeks 2
> through 6 are about those implementations — and that is the whole rest of the course."

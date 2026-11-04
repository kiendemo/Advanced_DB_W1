# Week 1 Lab Part A — Solution key & facilitator notes

**Facilitator copy. Do not release before the lab.** Release with the reflection at T+1 week.

All timings below were measured on the reference machine (24-core x86-64 Linux, warm page
cache, DuckDB 2.0.0, SQLite 3.41.2, TPC-H **sf=0.1**). **Students' absolute numbers will
differ; the ratios and their ordering are what reproduce.** Do not mark against the
milliseconds.

---

## Task 1 — `solutions/q1.sql`

Expected output (4 rows):

| l_returnflag | l_linestatus | cnt | sum_qty | sum_price | avg_disc |
|---|---|---|---|---|---|
| A | F | 147,790 | 3,774,200 | 5,320,753,880.69 | 0.0501 |
| N | F | 3,765 | 95,257 | 133,737,795.84 | 0.0494 |
| N | O | 291,817 | 7,454,519 | 10,505,523,577.97 | 0.0501 |
| R | F | 148,301 | 3,785,523 | 5,337,950,526.47 | 0.0500 |

**Q1.1 — `WHERE` or `HAVING`?**
`WHERE` is correct. `l_shipdate` is a property of an individual line item, so the predicate
must be applied **before** groups are formed. Putting it in `HAVING` is *not* merely
wasteful — it is **rejected**, because `l_shipdate` is neither a grouping column nor
aggregated, so after grouping it does not exist as a single value.
*Accept the stronger answer:* `HAVING MAX(l_shipdate) <= '1998-09-01'` **would** parse, but
it asks a completely different question — *keep groups in which every line item shipped by
that date* — and returns 1 row, not 4. Students who find this have understood `HAVING`
properly; give credit.

> **Common wrong answer.** Omitting the `WHERE` entirely. `cnt` for `N|O` becomes 300,716
> instead of 291,817. The autograder names the row and the number.

**Q1.2 — Why *must* both engines agree?**
Because SQL is declarative: the query specifies a result, not a procedure. The optimiser
may choose any plan from the space of plans it can prove **semantically equivalent**; cost
is the only thing it is allowed to optimise. Two engines with completely different storage
layouts and execution models are two points in that space. If they disagreed, one would
have a correctness bug. *(This is quiz Q7 made concrete, and it is the premise the rest of
the lab rests on — do not let the class skip it.)*

---

## Task 2 — `solutions/q2.sql`, `solutions/q2_fixed_grain.sql`

Top 3 of 10 rows: `8362 / ROMANIA / 35 / 5,793,605.05`, `6958 / ETHIOPIA / 30 /
5,370,682.19`, `9454 / MOZAMBIQUE / 35 / 5,354,381.81`.
4,439 of the 10,000 order-placing customers pass `HAVING COUNT(*) > 15`.

> Note for the debrief: `orders` has only **10,000 distinct** `o_custkey` but `customer`
> has **15,000** rows. 5,000 customers have never ordered, and the inner join silently
> drops them. Worth 20 seconds — it is quiz Q4 in the data in front of them.

**Q2.1 — What must `GROUP BY` contain?**
All three of `c_custkey`, `c_name`, `n_name`. The SQL standard requires every
non-aggregated `SELECT` expression to appear in `GROUP BY`; it does **not** reason about
functional dependencies in general, even though `c_custkey → c_name` genuinely holds here.
DuckDB enforces this. **SQLite does not** — it will accept `GROUP BY c.c_custkey` and
invent a value. Demonstrate the difference live if you have 30 seconds: it is quiz Q9, and
it is the better argument for why permissive engines cause production bugs.
*(Postgres 10+ and DB2 do infer the dependency from a declared primary key, so the strict
answer is "the standard does not require engines to infer it". Accept that nuance.)*

**Q2.2 — Why the tie-break?**
`ORDER BY total_value DESC` alone is a **partial** order. If two customers tie on
`total_value`, which one lands in the top 10 is decided by the plan, not the query — so the
same query on the same data can return different rows (quiz Q5). Adding `c_custkey ASC`
makes the order **total**, which makes `LIMIT 10` deterministic and therefore gradeable.
*In this dataset no two of the top customers actually tie,* so a student who omits it still
gets the right answer today. Say so — "correct by luck" is the lesson, and it is exactly
how this class of bug survives into production.

**Q2.3 — The grain trap.**
Adding `JOIN lineitem l ON l.l_orderkey = o.o_orderkey` makes each `orders` row appear once
per line item. `COUNT(*)` then counts **line items, not orders**, and `SUM(o_totalprice)`
adds each order's price once per line item. TPC-H generates 1–7 line items per order,
averaging 4, so both inflate by **≈4×** — and *non-uniformly*, since the factor is each
order's own line count. `HAVING COUNT(*) > 15` now also means something different.

The rule: **a join changes the grain of the result, and every aggregate is computed at
whatever grain reaches it.** The fix is to aggregate each grain separately before combining
— see `q2_fixed_grain.sql`, which pre-aggregates `lineitem` per `l_orderkey` in a CTE so the
join back to `orders` is 1:1 and `SUM(o_totalprice)` is safe again.

Accept any of: a pre-aggregating CTE/derived table (best), a correlated scalar subquery for
the line count, or `SUM(DISTINCT …)` **only if** the student notices it is wrong in general
(two orders can legitimately share a `o_totalprice`, and `DISTINCT` would then drop one).
Window functions are also fine but are not needed.

---

## Task 3 — the NULL anti-join

**(a)** `0`. Both engines. The standard requires it.

**(b)** `solutions/q3_diagnose.sql` → `total_rows=42, non_null_keys=40, null_keys=2`.

The argument: `x NOT IN (S)` expands to `x <> s₁ AND x <> s₂ AND … AND x <> sₙ`. For the
NULL element, `x <> NULL` evaluates to **UNKNOWN**, not FALSE. And
`TRUE AND UNKNOWN = UNKNOWN`. `WHERE` admits a row only on **TRUE**, so every row is
rejected and the count is 0 — *regardless of the 150,000 rows' actual key values*. A single
NULL in the subquery annihilates the entire result.

The dangerous property to name out loud: **this is not an error, it is a wrong answer.**
Nothing warns you. A report silently shows zero held-free orders.

**(c)** All three return **149,960** (= 150,000 − 40 distinct real held keys).

| | file | robust? |
|---|---|---|
| i | `q3_notexists.sql` | **yes, by construction** |
| ii | `q3_antijoin.sql` | **yes, by construction** |
| iii | `q3.sql` | correct, but only while someone remembers the filter |

**(d) — Which would you ship?** `NOT EXISTS` (or the anti-join). The reasoning that earns
full marks is not "it is faster" but **"it cannot break when the data changes."** With
`NOT EXISTS`, a NULL `ho_orderkey` simply fails the correlation predicate `h.ho_orderkey =
o.o_orderkey`, so that row matches nothing and suppresses nothing. The `NOT IN` + `IS NOT
NULL` version is correct today and silently wrong the day someone edits the subquery,
adds a column, or reuses it in a view. Robust **by construction** beats robust **by
vigilance** — that distinction is the point of the task.

> **Marking note.** A student who answers only "NOT EXISTS is faster" has missed it. On
> this data all three run in a few ms; performance is not the argument.

**(e) — Bridge to Part B.** The expected answer: **SQL is not relational algebra.** The
algebra's anti-join is set difference `orders − held_order`, total and well-defined, with no
NULL and no third truth value. SQL adds NULLs and three-valued logic for pragmatic reasons
(missing data, outer joins), and in doing so it **gives up equivalences that hold in the
algebra** — here, that `NOT IN` over a set and set difference should coincide. So SQL is an
*extension* of the relational model that is not a conservative one. **Part B should open on
this sentence.**

### Common wrong answers on Task 3

| What they write | Result | What to say |
|---|---|---|
| `LEFT JOIN … WHERE h.ho_reason IS NULL` | **149,961** | Tests `IS NULL` on a *non-key* column. We planted one real held key with a NULL reason so this is caught. Test the **join key**. |
| `NOT IN (… WHERE ho_orderkey <> NULL)` | 0 | `<> NULL` is UNKNOWN too — the filter removes everything. Must be `IS NOT NULL`. |
| `NOT EXISTS (SELECT 1 FROM held_order)` (uncorrelated) | 0 | No correlation → the subquery is non-empty → `NOT EXISTS` is false for every row. |
| Hardcoding 149960 | — | Grader rejects the literal. |

---

## Task 4 — measured reference numbers

Observed over **9 runs** on the reference machine. Quote the **range** to students, never a
point value — the medians are stable but the ratios are not, because DuckDB's absolute
times are single-digit milliseconds and it parallelises across all cores.

| Query | DuckDB | SQLite | Speed-up (range over 9 runs) | Winner |
|---|---|---|---|---|
| `S1-scan-agg` | ~4 ms | ~146 ms | **34–36×** (tight) | DuckDB |
| `S2-scan-agg-filtered` | ~6 ms | ~465 ms | **70–85×**, occasional outlier to ~170× | DuckDB |
| `S3-one-column` | ~0.4 ms | ~21 ms | **49–60×** | DuckDB |
| `P1-point-order` | ~0.65 ms | ~0.003 ms | **185–230×** | SQLite |
| `P2-point-customer` | ~0.21 ms | ~0.002 ms | **82–96×** | SQLite |

**Marking consequence.** Accept anything within roughly a factor of 3 of these, in the
right direction. A student reporting S1 at 100× is not wrong — on a quiet machine with
fewer cores we have seen exactly that. **What must be right is the direction of each row
and the ordering S3 > S1** (see below). The harness prints a `+/-` spread column and warns
when variance exceeds 40%; students who quote that spread in their write-up are doing it
properly.

**4b — the scan direction.** Two independent mechanisms, and students must give both:

1. **Bytes read (storage layout).** `lineitem` has 16 columns; S1 needs 5 (`l_returnflag`, `l_linestatus`,
   `l_quantity`, `l_extendedprice`, `l_discount`), S2 needs 6, S3 needs 1. A
   column store reads only the columns referenced — *projection pushdown* is free, because
   the unreferenced columns are in different blocks entirely. A row store must read whole
   tuples off the page to get at one field, so it pays for all 16 either way. Columnar data
   also compresses far better (run-length/dictionary on `l_returnflag`, which has **3** distinct
   values over 600,572 rows, and `l_linestatus`, which has **2**), shrinking the bytes further.
2. **Work per value (execution model).** DuckDB's operators consume **vectors** of ~2048
   values: one function call amortised over thousands of values, tight loops over typed
   arrays, no per-tuple interpretation, good cache and SIMD behaviour. SQLite pulls **one
   row at a time** through a bytecode VM; per row it pays interpreter dispatch, value
   unpacking and per-column type decoding.

*The quantitative check:* S3 (1 column) → **49–60×**; S1 (5 columns) → **34–36×**. This
ordering held in **all 9** reference runs, so it is the one quantitative claim you can mark
strictly. The gap **narrows**
as the query touches more columns, which is what the bytes-read argument predicts: the more
columns you need, the less a column store saves, and in the limit of `SELECT *` the
advantage goes away. Reason 2 is what remains at that limit — that is why the ratio narrows
rather than collapsing to 1×.

> Full marks require the quantitative step. Many students will assert both mechanisms and
> never check which one the data supports. **Checking is the skill.**

**4c — the point direction.** For `o_orderkey = 300001`, SQLite descends a B-tree: ~3 page
reads, finds the row, and because storage is row-oriented, **all of that row's columns are
already on that page** — one page, done. Microseconds. Total work is O(log n) and
independent of table size.
DuckDB has no secondary index here. Its minimum unit of work is a **row group** (on the
order of 10^5 rows — the exact constant is a DuckDB build parameter, so do not quote a
figure); zone maps let it skip row groups whose min/max cannot contain the key, but it must
still scan within the surviving group and reassemble the tuple from `orders`' 9 separate
column segments. Milliseconds.

The fair question, which the task asks deliberately: **would an index close the gap?** Yes,
partly — DuckDB supports ART indexes, and `CREATE INDEX` on `o_orderkey` improves point
lookups. But the absence is a **design choice, not an oversight**:
- an OLAP workload's queries touch large row fractions, where an index is useless or
  actively harmful (**you just measured that in 4d**);
- secondary indexes must be maintained on every write, which penalises the bulk-load and
  append patterns analytics systems are built around;
- indexes are poorly compressible random-access structures, in tension with the large
  sequential compressed scans the whole architecture is tuned for.
So the honest conclusion is **not** "column stores are bad at point lookups"; it is
"a system is a bundle of co-designed choices, and reading one benchmark number without the
design rationale tells you nothing." That sentence is the CLO1 outcome.

**4d — the optimiser mistake.** Plans:

```
S2:  SEARCH lineitem USING INDEX idx_lineitem_ship (l_shipdate<?)   +  TEMP B-TREE FOR GROUP BY
S2 NOT INDEXED:  SCAN lineitem                                      +  TEMP B-TREE FOR GROUP BY
```

Measured: S1 ~144 ms · S2 ~**460 ms — 3.1–3.2× slower than S1 while doing strictly less
work** · S2 with `NOT INDEXED` ~144 ms, i.e. **~3.2× recovered**, back to the S1 baseline.
These three SQLite numbers are stable to within a few percent across runs (SQLite is
single-threaded, so it is the quiet half of this experiment) — mark them strictly.

Why the index is catastrophic at 98.5% selectivity: for each of 591,673 matching index
entries SQLite gets a **rowid**, and the index does **not** contain `l_returnflag`,
`l_linestatus`, `l_quantity`, `l_extendedprice` or `l_discount`. So per row it must do a
separate lookup into the table B-tree to fetch the rest of the tuple. That is ~592k
**random** page accesses in rowid-unordered sequence, instead of one **sequential** scan of
the same pages. Sequential access wins on every level of the memory hierarchy — prefetch,
page locality, TLB — and here the index has converted a sequential scan into a random one
while *also* reading the index. An index pays off only when it eliminates enough rows to
offset the random-access cost; the rule of thumb is a few percent selectivity, and 98.5% is
not that.

The root cause is a **cardinality/selectivity estimation error**: SQLite's cost model
assumed the range predicate was selective. This is exactly the Week 5–6 material, found in
Week 1.

> **Bonus, if a sharp student runs `--explain` on DuckDB too.** DuckDB's plan reports
> `~120,114 rows` for the same filter whose true cardinality is **591,673** — it is wrong by
> about 5×, in the *same direction* as SQLite. So the lesson is sharper than "SQLite's
> optimiser is bad": **both** optimisers misestimate this predicate, and only one of them
> had a choice it could get catastrophically wrong. Estimation error is universal; what
> differs is how much damage the plan space lets it do. If a student finds this
> unprompted, that is extension-level insight — say so.

**4.** DuckDB goes ~4 → ~6 ms, essentially unchanged, because **it had no index to
choose wrongly**. Its plan is the same full vectorised scan with the filter pushed into it;
the predicate costs a little extra CPU and saves a little aggregation. Fewer choices means
fewer ways to be catastrophically wrong — predictability is itself an architectural
property, and a defensible reason an OLAP engine ships without secondary indexes.

**4e — the resolution, and why column stores exist.** Measured:

```
SELECT COUNT(*) … WHERE l_shipdate <= …                 7.52 ms   SEARCH … USING COVERING INDEX
SELECT COUNT(*) … NOT INDEXED WHERE l_shipdate <= …    22.61 ms   SCAN lineitem
```

The index is **3× faster** here and ~60× slower in 4d, from the same index on the same
predicate. The only difference is **which columns the query needs**. `COUNT(*)` with a
predicate on `l_shipdate` needs *nothing but* `l_shipdate` — which is in the index. SQLite
says so in one word: `COVERING INDEX`. No table access at all. In 4d the query needed five
more columns, none of them in the index, so every row cost a random table fetch.

The payoff sentence: a covering index stores *one subset of columns, contiguously, without
the rest of the row* — which **is** a column store, hand-built, for one query shape. It
reads less and scans sequentially for exactly the same reason. The difference is that a
column store gives you this **for every column at once, by default**, with compression, and
without the write amplification and storage cost of maintaining a separate B-tree per query
shape. Accept any answer that reaches "a covering index is a per-query-shape column
projection, and a column store generalises it."

**4f — the conclusion paragraph.** Full marks need a *workload-shaped* criterion, not a
product preference. Look for: **row fraction touched** (few rows → row store), **column
fraction touched** (few of many columns → column store), **write pattern** (many small
point writes → row store; bulk append → column store), **latency target** (sub-ms point
lookups → row store), and ideally the observation that real systems are **HTAP** attempts to
have both. Must cite their own measurements.

---

## Extension — what a good answer looks like

**E1.** Point-lookup-shaped queries for SQLite (`WHERE pk = …`, `SELECT *` on one row) and
wide-scan aggregates for DuckDB (`SUM` over `lineitem`). At sf=1 the DuckDB:SQLite scan
ratio should **hold or grow** (both are linear in rows, but DuckDB parallelises across cores
while SQLite is single-threaded, and compression improves with more data). The point-lookup
ratio should **shrink slightly or hold**: SQLite's B-tree grows only logarithmically, while
DuckDB's scan cost grows with the number of row groups — so this one can actually move in
SQLite's favour. Credit the *prediction with a mechanism*, not the number.

**E2.** `CREATE INDEX idx_cover ON lineitem(l_returnflag, l_linestatus, l_quantity,
l_extendedprice, l_discount)` takes S1 from **143.6 ms → 31.9 ms** (4.5×), plan
`SCAN lineitem USING COVERING INDEX idx_cover`. Still **~8× slower** than DuckDB's 4.05 ms.
The two things you cannot get this way: (1) **compression and vectorised execution** — the
index is still a row-structured B-tree traversed tuple-at-a-time, so you saved bytes but not
per-value interpretation; (2) **generality without cost** — this index helps *this* query
shape only, and you pay for it on every insert and in storage. A second query shape needs a
second index. That is the write-amplification argument for column stores.

**E3.** Any second instance with plan + fix + stated selectivity error. Note honestly that
`ANALYZE` has **already** been run by `build_data.py`, so "run ANALYZE" will often *not*
fix it — the interesting finding is that fresh statistics are not sufficient, because
SQLite's `sqlite_stat1` keeps only coarse per-index averages and cannot represent the
distribution of a range predicate. Credit students who discover and explain that; it is a
genuine limitation and a direct lead into Week 6.

**E4.** The honest expected result: on sf=0.1 both databases **already fit in the page
cache**, so a RAM disk changes little and the workload is **CPU-bound**, not I/O-bound.
That is the valuable finding — it shows that "in-memory" is an *architectural* claim about
data layout, no-buffer-pool access paths and pointer-based access, not merely "the data
happens to be cached." Students who report "no significant change" **with that
interpretation** get full marks. Students who report no change and conclude "in-memory
systems are pointless" have missed it. (Pushing them to sf=1 or sf=5 so the data exceeds
cache is the natural follow-up.)

---

## If you are running out of time

Cut in this order — later items cost the most learning per minute saved:

1. **Task 2 Q2.3** → set as take-home. (Costs the grain lesson; the autograder still checks it.)
2. **Task 4e** → set as take-home. (The best single insight in the lab — cut reluctantly.)
3. **Task 1** → have the class run it and read off the numbers without writing it. (It is
   the warm-up and the env check; keep the run, drop the authoring.)
4. **Quiz Q9/Q10** → already marked spare.

**Never cut:** Task 3 (a)–(c), Task 4a–4c, Task 4d. Those four are the lab's spine: the
silent-wrong-answer, the bidirectional measurement, and the optimiser mistake.

#!/usr/bin/env python3
"""
COMP5330 Week 1 Lab -- Task 4 timing harness.

Runs the SAME SQL string against DuckDB (columnar) and SQLite (row-oriented)
and reports timings. Methodology, which matters as much as the numbers:

  * one connection per engine, opened once -- connection setup is not query time
  * one warm-up execution per query, discarded -- we measure warm cache, not cold I/O
  * the warm-up also SIZES the experiment: we pick the repetition count so each
    (engine, query) pair gets ~0.4 s of timed work, bounded to [5, 50] reps. A query
    that takes 0.5 ms gets many more repetitions than one taking 450 ms, which is
    how you get comparable confidence out of times that differ by 1000x.
  * we report the MEDIAN, and a SPREAD column: (p90 - p10) / median, as a percent.
    A single number is not a measurement. If spread is large, say so in your
    write-up rather than quoting the median as if it were exact.
  * results are fully materialised with fetchall(), because DuckDB is lazy and
    timing a query you never consumed measures nothing

Usage
-----
    python starter/bench.py                 # run the Task 4 query set
    python starter/bench.py --sql "SELECT COUNT(*) FROM lineitem"
    python starter/bench.py --explain       # also print both query plans
    python starter/bench.py --reps 15
"""
import argparse
import os
import sqlite3
import statistics
import time

DUCK = os.path.join("data", "tpch.duckdb")
SQLT = os.path.join("data", "tpch.sqlite")

QUERIES = {
    "S1-scan-agg": """
        SELECT l_returnflag, l_linestatus, COUNT(*) AS cnt,
               SUM(l_quantity) AS sum_qty, SUM(l_extendedprice) AS sum_price,
               AVG(l_discount) AS avg_disc
        FROM lineitem
        GROUP BY l_returnflag, l_linestatus
        ORDER BY l_returnflag, l_linestatus""",

    "S2-scan-agg-filtered": """
        SELECT l_returnflag, l_linestatus, COUNT(*) AS cnt,
               SUM(l_quantity) AS sum_qty, SUM(l_extendedprice) AS sum_price,
               AVG(l_discount) AS avg_disc
        FROM lineitem
        WHERE l_shipdate <= '1998-09-01'
        GROUP BY l_returnflag, l_linestatus
        ORDER BY l_returnflag, l_linestatus""",

    "S3-one-column": "SELECT SUM(l_extendedprice) FROM lineitem",

    "P1-point-order": "SELECT * FROM orders WHERE o_orderkey = 300001",

    "P2-point-customer": "SELECT c_name, c_acctbal FROM customer WHERE c_custkey = 9001",
}


def timed(con, sql, reps=None, budget=0.4):
    """Return (median_ms, spread_pct, nrows, reps_used)."""
    # Three warm-up executions, all discarded. One is not enough: DuckDB spins up a
    # worker thread per core on first use, and that shows up as a slow first run.
    for _ in range(3):
        t0 = time.perf_counter()
        rows = con.execute(sql).fetchall()
        warm = time.perf_counter() - t0

    if reps is None:                                  # size the experiment
        reps = int(budget / warm) if warm > 0 else 50
        reps = max(5, min(50, reps))

    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        rows = con.execute(sql).fetchall()
        ts.append((time.perf_counter() - t0) * 1000.0)

    ts.sort()
    med = statistics.median(ts)
    lo = ts[int(0.10 * (len(ts) - 1))]
    hi = ts[int(0.90 * (len(ts) - 1))]
    spread = (hi - lo) / med * 100.0 if med else 0.0
    return med, spread, len(rows), reps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", help="run one ad-hoc query instead of the Task 4 set")
    ap.add_argument("--reps", type=int, default=None,
                    help="fixed repetition count (default: sized automatically)")
    ap.add_argument("--explain", action="store_true", help="print both query plans")
    args = ap.parse_args()

    import duckdb
    for p in (DUCK, SQLT):
        if not os.path.exists(p):
            raise SystemExit(f"{p} missing -- run: python setup/build_data.py")

    dc = duckdb.connect(DUCK, read_only=True)
    sc = sqlite3.connect(SQLT)

    todo = {"ad-hoc": args.sql} if args.sql else QUERIES

    print(f"{'query':<22} {'DuckDB med':>11} {'+/-':>5} {'SQLite med':>11} {'+/-':>5} "
          f"{'speed-up':>10}  {'winner':<7} {'rows':>5}")
    print("-" * 88)
    noisy = []
    for name, sql in todo.items():
        dmed, dspr, dn, dreps = timed(dc, sql, args.reps)
        smed, sspr, sn, sreps = timed(sc, sql, args.reps)
        flag = "" if dn == sn else f"  <-- ROW COUNTS DIFFER {dn} vs {sn}"
        if smed >= dmed:
            speedup, winner = smed / dmed, "DuckDB"
        else:
            speedup, winner = dmed / smed, "SQLite"
        print(f"{name:<22} {dmed:9.3f}ms {dspr:4.0f}% {smed:9.3f}ms {sspr:4.0f}% "
              f"{speedup:9.1f}x  {winner:<7} {dn:>5}{flag}")
        if max(dspr, sspr) > 40:
            noisy.append(name)

        if args.explain:
            print(f"\n  --- DuckDB plan for {name} ---")
            for r in dc.execute("EXPLAIN " + sql).fetchall():
                print("   ", r[-1].replace("\n", "\n    "))
            print(f"  --- SQLite plan for {name} ---")
            for r in sc.execute("EXPLAIN QUERY PLAN " + sql).fetchall():
                print("   ", r)
            print()

    print("\nThe speed-up column is always >= 1x; read it together with 'winner'.")
    print("'+/-' is (p90-p10)/median: how noisy that measurement was on YOUR machine.")
    print("Record the MEDIAN columns in your handout table.")
    print("Timings are hardware- and cache-dependent: compare RATIOS, not milliseconds.")
    if noisy:
        print(f"\nNOTE: high variance (>40%) on {', '.join(noisy)}.")
        print("  DuckDB runs scans across all your cores, so a few-millisecond query is")
        print("  sensitive to scheduler jitter and to whatever else your laptop is doing.")
        print("  Close other applications, plug in the power, and re-run. Expect the scan")
        print("  ratios to move by 2-3x between runs even so -- which is exactly why the")
        print("  handout asks you for an ORDER OF MAGNITUDE and a mechanism, not a number.")


if __name__ == "__main__":
    main()

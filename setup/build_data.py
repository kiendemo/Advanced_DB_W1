#!/usr/bin/env python3
"""
COMP5330 Week 1 Lab -- dataset builder.

Builds the SAME data in two engines with two different storage architectures:

  tpch.duckdb   DuckDB   -- columnar, vectorised, no secondary indexes  (OLAP-shaped)
  tpch.sqlite   SQLite   -- row-oriented B-tree, PK indexes created     (OLTP-shaped)

Data is GENERATED locally by DuckDB's TPC-H extension, so there is no large
download and the result is bit-for-bit reproducible from the scale factor.

Also creates one small table, held_order, that deliberately contains NULLs.
It is the subject of Task 3 -- do not "clean" it.

Usage
-----
    python setup/build_data.py                 # scale factor 0.1  (default, ~1 min)
    python setup/build_data.py --sf 1          # 10x bigger, for the extension task
    python setup/build_data.py --outdir data

Requires: pip install duckdb      (first run also downloads the tpch extension)
"""

import argparse
import os
import re
import random
import sqlite3
import sys
import time

TABLES = [
    "region", "nation", "supplier", "customer",
    "part", "partsupp", "orders", "lineitem",
]

# Secondary structures we give SQLite so the OLTP comparison in Task 4 is fair.
# Without these, SQLite would full-scan for a point lookup and the lab would
# be comparing "indexed vs unindexed", not "row-store vs column-store".
SQLITE_INDEXES = [
    ("region",   "CREATE UNIQUE INDEX idx_region_pk   ON region(r_regionkey)"),
    ("nation",   "CREATE UNIQUE INDEX idx_nation_pk   ON nation(n_nationkey)"),
    ("supplier", "CREATE UNIQUE INDEX idx_supplier_pk ON supplier(s_suppkey)"),
    ("customer", "CREATE UNIQUE INDEX idx_customer_pk ON customer(c_custkey)"),
    ("part",     "CREATE UNIQUE INDEX idx_part_pk     ON part(p_partkey)"),
    ("partsupp", "CREATE UNIQUE INDEX idx_partsupp_pk ON partsupp(ps_partkey, ps_suppkey)"),
    ("orders",   "CREATE UNIQUE INDEX idx_orders_pk   ON orders(o_orderkey)"),
    ("lineitem", "CREATE INDEX        idx_lineitem_pk ON lineitem(l_orderkey, l_linenumber)"),
    ("lineitem", "CREATE INDEX        idx_lineitem_ship ON lineitem(l_shipdate)"),
]


def log(msg):
    print(f"[build] {msg}", flush=True)


def duck_type_to_cast(col, typ):
    """
    Return a SELECT expression for `col` that SQLite's Python driver can bind.

    DuckDB hands back datetime.date for DATE and decimal.Decimal for DECIMAL;
    sqlite3 refuses to bind Decimal, and the implicit date adapter is deprecated
    in Python 3.12+. So we normalise inside SQL instead: dates become ISO-8601
    TEXT (which still compares correctly with <, >, BETWEEN in SQLite) and
    decimals become DOUBLE.
    """
    t = typ.upper()
    if t.startswith("DATE") or t.startswith("TIMESTAMP"):
        return f'CAST("{col}" AS VARCHAR) AS "{col}"'
    if t.startswith("DECIMAL") or t.startswith("NUMERIC"):
        return f'CAST("{col}" AS DOUBLE) AS "{col}"'
    return f'"{col}"'


def sqlite_decl(typ):
    t = typ.upper()
    if t.startswith(("DATE", "TIMESTAMP", "VARCHAR", "CHAR", "TEXT", "BLOB")):
        return "TEXT"
    if t.startswith(("DECIMAL", "NUMERIC", "DOUBLE", "FLOAT", "REAL")):
        return "REAL"
    return "INTEGER"


def build_duckdb(path, sf):
    import duckdb

    if os.path.exists(path):
        os.remove(path)
    con = duckdb.connect(path)
    log(f"generating TPC-H sf={sf} into {path} ...")
    t0 = time.perf_counter()
    con.execute("INSTALL tpch")
    con.execute("LOAD tpch")
    con.execute(f"CALL dbgen(sf={sf})")
    log(f"  dbgen done in {time.perf_counter() - t0:.1f}s")

    # ---- the deliberately dirty table (Task 3) --------------------------------
    # Story for students: "orders flagged by the fraud-review system". A buggy
    # ETL job wrote some rows with a NULL order key. That single NULL is enough
    # to make a NOT IN anti-join return the empty set.
    n_orders = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    rng = random.Random(5330)          # fixed seed => same table for everyone
    sample = con.execute(
        "SELECT o_orderkey FROM orders ORDER BY o_orderkey LIMIT 40 OFFSET 7"
    ).fetchall()
    held = [r[0] for r in sample]
    con.execute("CREATE TABLE held_order (ho_orderkey BIGINT, ho_reason VARCHAR)")
    reasons = ["velocity", "geo_mismatch", "manual_review", "chargeback_history"]
    rows = [(k, rng.choice(reasons)) for k in held]
    # Landmine 1: a NULL JOIN KEY. This is what breaks NOT IN (Task 3).
    rows.insert(13, (None, "manual_review"))
    rows.append((None, None))
    # Landmine 2: a REAL key whose *reason* is NULL. This exists so that the
    # near-miss anti-join -- LEFT JOIN ... WHERE h.ho_reason IS NULL -- gives a
    # different (wrong) count than the correct WHERE h.ho_orderkey IS NULL.
    # Without this row the two are accidentally equal and the bug stays hidden.
    rows[5] = (rows[5][0], None)
    con.executemany("INSERT INTO held_order VALUES (?, ?)", rows)
    log(f"  held_order: {len(rows)} rows, "
        f"{sum(1 for r in rows if r[0] is None)} with NULL ho_orderkey, "
        f"{sum(1 for r in rows if r[0] is not None and r[1] is None)} real key with NULL reason")

    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in TABLES + ["held_order"]}
    con.close()
    return counts, n_orders


def export_sqlite(duck_path, sqlite_path, batch=50_000):
    import duckdb

    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    src = duckdb.connect(duck_path, read_only=True)
    dst = sqlite3.connect(sqlite_path)
    dst.execute("PRAGMA journal_mode=OFF")
    dst.execute("PRAGMA synchronous=OFF")

    for tbl in TABLES + ["held_order"]:
        info = src.execute(f'PRAGMA table_info("{tbl}")').fetchall()
        names = [r[1] for r in info]
        types = [r[2] for r in info]
        ddl_cols = ", ".join(f'"{n}" {sqlite_decl(t)}' for n, t in zip(names, types))
        dst.execute(f'CREATE TABLE "{tbl}" ({ddl_cols})')

        sel = ", ".join(duck_type_to_cast(n, t) for n, t in zip(names, types))
        placeholders = ", ".join("?" * len(names))
        ins = f'INSERT INTO "{tbl}" VALUES ({placeholders})'

        t0, n = time.perf_counter(), 0
        cur = src.execute(f'SELECT {sel} FROM "{tbl}"')
        while True:
            rows = cur.fetchmany(batch)
            if not rows:
                break
            dst.executemany(ins, rows)
            n += len(rows)
        dst.commit()
        log(f"  {tbl:<10} {n:>9,} rows -> sqlite in {time.perf_counter() - t0:.1f}s")

    log("creating SQLite indexes (this is what makes it an OLTP store) ...")
    for tbl, stmt in SQLITE_INDEXES:
        t0 = time.perf_counter()
        dst.execute(stmt)
        name = re.search(r"INDEX\s+(\w+)", stmt).group(1)
        log(f"  {name:<20} {time.perf_counter() - t0:.1f}s")
    dst.commit()
    dst.execute("ANALYZE")
    dst.commit()
    dst.close()
    src.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sf", type=float, default=0.1,
                    help="TPC-H scale factor (0.1 default; 1 for the extension task)")
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--skip-sqlite", action="store_true")
    args = ap.parse_args()

    try:
        import duckdb  # noqa: F401
    except ImportError:
        sys.exit("ERROR: duckdb not installed.  Run:  pip install duckdb")

    os.makedirs(args.outdir, exist_ok=True)
    tag = "" if args.sf == 0.1 else f"-sf{args.sf:g}"
    duck_path = os.path.join(args.outdir, f"tpch{tag}.duckdb")
    sqlite_path = os.path.join(args.outdir, f"tpch{tag}.sqlite")

    t0 = time.perf_counter()
    counts, _ = build_duckdb(duck_path, args.sf)
    if not args.skip_sqlite:
        log(f"exporting to {sqlite_path} ...")
        export_sqlite(duck_path, sqlite_path)

    print()
    log("row counts")
    for t, c in counts.items():
        print(f"         {t:<12} {c:>10,}")
    print()
    for p in (duck_path, sqlite_path):
        if os.path.exists(p):
            log(f"{p:<30} {os.path.getsize(p) / 1e6:>8.1f} MB")
    log(f"total {time.perf_counter() - t0:.1f}s -- now run:  python setup/verify_setup.py")


if __name__ == "__main__":
    main()

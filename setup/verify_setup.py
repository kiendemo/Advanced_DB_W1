#!/usr/bin/env python3
"""
COMP5330 Week 1 Lab -- setup self-check.

Run this AT HOME, before the lab. It prints a one-line fingerprint.
Paste that line into the Canvas thread "Week 1 lab -- setup check" so we know
you are ready. If anything fails, the message tells you what to fix.

    python setup/verify_setup.py
"""
import os
import sys

DUCK = os.path.join("data", "tpch.duckdb")
SQLT = os.path.join("data", "tpch.sqlite")
EXPECT = {"region": 5, "nation": 25, "supplier": 1_000, "customer": 15_000,
          "part": 20_000, "partsupp": 80_000, "orders": 150_000,
          "lineitem": 600_572, "held_order": 42}

def fail(msg, fix):
    print(f"\n  FAIL  {msg}\n  FIX   {fix}\n")
    sys.exit(1)

def main():
    print("COMP5330 Week 1 lab -- setup check")
    print(f"  python {sys.version.split()[0]}")

    try:
        import duckdb
    except ImportError:
        fail("duckdb is not installed", "pip install duckdb")
    print(f"  duckdb {duckdb.__version__}")

    import sqlite3
    print(f"  sqlite {sqlite3.sqlite_version}")
    if sqlite3.sqlite_version_info < (3, 25, 0):
        fail("SQLite is older than 3.25", "upgrade Python, or use a newer sqlite3")

    for p in (DUCK, SQLT):
        if not os.path.exists(p):
            fail(f"{p} is missing", "python setup/build_data.py")

    d = duckdb.connect(DUCK, read_only=True)
    s = sqlite3.connect(SQLT)
    bad = []
    for t, n in EXPECT.items():
        dn = d.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        sn = s.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        if dn != n or sn != n:
            bad.append(f"{t}: duckdb={dn} sqlite={sn} expected={n}")
    if bad:
        fail("row counts are wrong:\n        " + "\n        ".join(bad),
             "delete the data/ directory and re-run setup/build_data.py")

    # The two engines must agree on the reference query, or the lab's whole
    # premise -- same SQL, same answer, different plan -- is broken.
    q = ("SELECT l_returnflag, l_linestatus, COUNT(*), ROUND(SUM(l_quantity),2) "
         "FROM lineitem WHERE l_shipdate <= '1998-09-01' "
         "GROUP BY l_returnflag, l_linestatus ORDER BY 1,2")
    dr = [(a, b, c, float(x)) for a, b, c, x in d.execute(q).fetchall()]
    sr = [(a, b, c, float(x)) for a, b, c, x in s.execute(q).fetchall()]
    if dr != sr:
        fail("the two engines disagree on the reference query",
             "delete data/ and re-run setup/build_data.py")

    nulls = d.execute("SELECT COUNT(*) FROM held_order WHERE ho_orderkey IS NULL").fetchone()[0]
    if nulls != 2:
        fail(f"held_order should contain exactly 2 NULL keys, found {nulls}",
             "delete data/ and re-run setup/build_data.py -- and do NOT clean this table")

    fp = f"{dr[0][2]}-{dr[-1][2]}-{int(dr[0][3])}-{nulls}"
    print(f"\n  OK  everything checks out.")
    print(f"  Paste this line into the Canvas setup thread:")
    print(f"\n      WEEK1-SETUP {fp}  (duckdb {duckdb.__version__}, sqlite {sqlite3.sqlite_version})\n")

if __name__ == "__main__":
    main()

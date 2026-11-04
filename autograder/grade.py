#!/usr/bin/env python3
"""
COMP5330 Week 1 Lab -- autograder for the SQL half.

Runs each answers/*.sql against DuckDB and checks the result against a reference
*property* rather than a stored output file. Checking properties (shape, key values,
determinism, NULL-robustness) instead of a golden file means a student who writes a
different-but-correct query still passes, and a student who hardcodes the answer fails.

    python autograder/grade.py            # grade everything
    python autograder/grade.py --task 3   # one task
    python autograder/grade.py --solutions  # self-test: grade the solution key

Exit code 0 if every graded check passes.
"""
import argparse
import glob
import os
import sys

DUCK = os.path.join("data", "tpch.duckdb")
ANSWERS = "answers"


# --------------------------------------------------------------------------- utils
GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""


class Check:
    def __init__(self):
        self.passed, self.failed, self.skipped = [], [], []

    def ok(self, name):
        self.passed.append(name)
        print(f"  {GREEN}PASS{RESET}  {name}")

    def no(self, name, why):
        self.failed.append((name, why))
        print(f"  {RED}FAIL{RESET}  {name}\n        {why}")

    def skip(self, name, why):
        self.skipped.append((name, why))
        print(f"  {YELLOW}SKIP{RESET}  {name}  {DIM}({why}){RESET}")


def read_sql(path):
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8").read()
    # strip line comments so "the answer is in a comment" doesn't count
    lines = [l for l in txt.splitlines() if not l.strip().startswith("--")]
    sql = "\n".join(lines).strip().rstrip(";").strip()
    return sql or None


def run(con, sql):
    cur = con.execute(sql)
    cols = [d[0].lower() for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


def num(x):
    from decimal import Decimal
    if isinstance(x, Decimal):
        return float(x)
    return x


def close(a, b, tol=0.01):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


# --------------------------------------------------------------------------- tasks
def grade_q1(con, c, srcdir):
    name = "Task 1 - TPC-H Q1 shape"
    sql = read_sql(os.path.join(srcdir, "q1.sql"))
    if sql is None:
        return c.skip(name, "q1.sql missing or empty")
    try:
        cols, rows = run(con, sql)
    except Exception as e:
        return c.no(name, f"query failed: {e}")

    if len(rows) != 4:
        return c.no(name, f"expected 4 groups, got {len(rows)} "
                          f"(did you forget WHERE l_shipdate <= '1998-09-01'?)")
    if len(cols) != 6:
        return c.no(name, f"expected 6 output columns, got {len(cols)}: {cols}")

    expect = [("A", "F", 147790, 3774200.0, 5320753880.69, 0.0501),
              ("N", "F", 3765, 95257.0, 133737795.84, 0.0494),
              ("N", "O", 291817, 7454519.0, 10505523577.97, 0.0501),
              ("R", "F", 148301, 3785523.0, 5337950526.47, 0.0500)]
    for i, (got, exp) in enumerate(zip(rows, expect)):
        g = [num(v) for v in got]
        if str(g[0]) != exp[0] or str(g[1]) != exp[1]:
            return c.no(name, f"row {i+1}: expected flag/status {exp[0]}/{exp[1]}, "
                              f"got {g[0]}/{g[1]} -- check your ORDER BY")
        if g[2] != exp[2]:
            return c.no(name, f"row {i+1} cnt: expected {exp[2]}, got {g[2]}")
        if not close(g[3], exp[3], 0.5):
            return c.no(name, f"row {i+1} sum_qty: expected {exp[3]}, got {g[3]}")
        if not close(g[4], exp[4], 1.0):
            return c.no(name, f"row {i+1} sum_price: expected {exp[4]}, got {g[4]}")
        if not close(g[5], exp[5], 0.0005):
            return c.no(name, f"row {i+1} avg_disc: expected ~{exp[5]}, got {g[5]} "
                              f"-- AVG(l_discount), not SUM")
    c.ok(name)


def grade_q2(con, c, srcdir):
    name = "Task 2 - top-10 customers, HAVING > 15 orders"
    sql = read_sql(os.path.join(srcdir, "q2.sql"))
    if sql is None:
        return c.skip(name, "q2.sql missing or empty")
    try:
        cols, rows = run(con, sql)
    except Exception as e:
        return c.no(name, f"query failed: {e}")

    if len(rows) != 10:
        return c.no(name, f"expected exactly 10 rows (LIMIT 10), got {len(rows)}")
    if len(cols) != 5:
        return c.no(name, f"expected 5 columns, got {len(cols)}: {cols}")

    head = [(8362, "ROMANIA", 35, 5793605.05),
            (6958, "ETHIOPIA", 30, 5370682.19),
            (9454, "MOZAMBIQUE", 35, 5354381.81)]
    for i, exp in enumerate(head):
        g = [num(v) for v in rows[i]]
        if g[0] != exp[0]:
            return c.no(name, f"row {i+1}: expected c_custkey {exp[0]}, got {g[0]} -- "
                              f"check ORDER BY total_value DESC, c_custkey ASC")
        if exp[1] not in [str(v) for v in g]:
            return c.no(name, f"row {i+1}: nation {exp[1]} not in the row -- "
                              f"did you join nation?")
        if exp[2] not in [v for v in g if isinstance(v, int)]:
            return c.no(name, f"row {i+1}: expected n_orders {exp[2]} -- "
                              f"if it is ~4x larger you joined lineitem (Q2.3)")
        if not any(close(v, exp[3], 1.0) for v in g if isinstance(v, (int, float))):
            return c.no(name, f"row {i+1}: expected total_value ~{exp[3]}")

    keys = [num(r[0]) for r in rows]
    if len(set(keys)) != 10:
        return c.no(name, "duplicate c_custkey in the output -- your GROUP BY is wrong")
    c.ok(name)


def grade_q3(con, c, srcdir):
    EXPECT = 149960
    variants = [
        ("q3.sql", "Task 3c-iii - NOT IN, NULL-free subquery", ["not in"], []),
        ("q3_notexists.sql", "Task 3c-i  - NOT EXISTS", ["not exists"], []),
        ("q3_antijoin.sql", "Task 3c-ii - LEFT JOIN anti-join", ["left join", "is null"], []),
        # NB: a near-miss here is `WHERE h.ho_reason IS NULL` -- IS NULL on a
        # non-key column. held_order contains one real key with a NULL reason
        # precisely so that this returns 149961 and is caught below.
    ]
    for fname, name, must, mustnot in variants:
        sql = read_sql(os.path.join(srcdir, fname))
        if sql is None:
            c.skip(name, f"{fname} missing or empty")
            continue
        low = " ".join(sql.lower().split())
        missing = [m for m in must if m not in low]
        if missing:
            c.no(name, f"this file must use {' and '.join(repr(m) for m in must)}; "
                       f"missing {missing}")
            continue
        if "149960" in low.replace(",", ""):
            c.no(name, "the expected count appears literally in your SQL -- "
                       "compute it, do not hardcode it")
            continue
        try:
            _, rows = run(con, sql)
        except Exception as e:
            c.no(name, f"query failed: {e}")
            continue
        if len(rows) != 1 or len(rows[0]) != 1:
            c.no(name, f"expected a single scalar count, got {len(rows)} rows "
                       f"x {len(rows[0]) if rows else 0} cols")
            continue
        got = num(rows[0][0])
        if got != EXPECT:
            hint = ""
            if got == 0:
                hint = " -- this is the NULL trap; your subquery still yields a NULL"
            elif got == 150000:
                hint = " -- you are excluding nothing; check the join/correlation predicate"
            elif got == EXPECT + 1:
                hint = (" -- off by one: you tested IS NULL on a non-key column of "
                        "held_order. Test it on the JOIN KEY (ho_orderkey)")
            c.no(name, f"expected {EXPECT}, got {got}{hint}")
            continue
        c.ok(name)


def grade_task4(con, c, srcdir):
    """
    Checks that each of sections 4b-4f actually contains the student's own prose.

    Counting words over the whole file is not enough: the stub template is itself
    ~200 words of headings and prompts, so an untouched stub would pass. We instead
    split on the section headings and, within each section, ignore headings, table
    rows, and the stub's parenthetical prompt lines.
    """
    import re as _re
    name = "Task 4 - written analysis present"
    path = os.path.join(srcdir, "task4.md")
    if not os.path.exists(path):
        return c.skip(name, "task4.md missing (hand-marked, 0 if absent)")
    txt = open(path, encoding="utf-8").read()

    # split into sections keyed by 4a..4f
    marks = [(m.start(), m.group(1).lower())
             for m in _re.finditer(r"4([a-f])\b", txt)]
    if not marks:
        return c.no(name, "no sections labelled 4a-4f found")
    sections = {}
    for i, (pos, key) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        sections.setdefault(key, "")
        sections[key] += txt[pos:end]

    def substantive(body):
        out = []
        for line in body.splitlines():
            t = line.strip()
            if not t or t.startswith("#") or t.startswith("|") or t.startswith("---"):
                continue
            if t.startswith("(") and t.endswith(")"):      # stub prompt line
                continue
            if t.endswith(":"):                            # stub label awaiting an answer
                continue
            if t.startswith('"') or t.startswith("Machine:"):
                continue
            t = _re.sub(r"^4[a-f]\b[^A-Za-z0-9]*", "", t)  # drop the label itself
            out.append(t)
        return " ".join(out)

    thin = []
    for key in ("b", "c", "d", "e", "f"):
        body = substantive(sections.get(key, ""))
        n = len(body.split())
        if n < 15:
            thin.append(f"4{key} ({n} words)")
    if thin:
        return c.no(name, "these sections have no real answer yet: "
                          + ", ".join(thin)
                          + "\n        (headings, table rows and the stub's prompt lines "
                            "do not count -- write your own prose)")

    total = sum(len(substantive(sections.get(k, "")).split()) for k in "bcdef")
    c.ok(name + f" ({total} words of prose across 4b-4f -- hand-marked for content)")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--solutions", action="store_true",
                    help="grade solutions/ instead of answers/ (self-test)")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        sys.exit("ERROR: duckdb not installed.  pip install duckdb")
    if not os.path.exists(DUCK):
        sys.exit(f"ERROR: {DUCK} missing.  python setup/build_data.py")

    if args.solutions:
        srcdir = "solutions"
    else:
        # accept answers/ (the documented layout) or starter/answers/
        srcdir = next((d for d in (ANSWERS, os.path.join("starter", "answers"))
                       if os.path.isdir(d)), None)
    if not srcdir or not os.path.isdir(srcdir):
        sys.exit("ERROR: no answers/ directory here. Run this from the lab root "
                 "(the directory containing setup/, handout/ and answers/).")

    con = duckdb.connect(DUCK, read_only=True)
    c = Check()
    print(f"COMP5330 Week 1 lab -- grading {srcdir}/\n")
    for n, fn in ((1, grade_q1), (2, grade_q2), (3, grade_q3), (4, grade_task4)):
        if args.task in (None, n):
            fn(con, c, srcdir)

    total = len(c.passed) + len(c.failed)
    print(f"\n  {len(c.passed)}/{total} checks passed"
          + (f", {len(c.skipped)} skipped" if c.skipped else ""))
    if c.failed:
        print(f"\n{RED}Not finished yet.{RESET} Fix the FAILs above and re-run.")
        return 1
    if c.skipped:
        print(f"\n{YELLOW}Everything attempted is correct, but files are missing.{RESET}")
        return 0
    print(f"\n{GREEN}All checks passed.{RESET} Task 4 prose is still hand-marked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Week 1 Lab — Setup

**Do this at home, before Friday.** It needs about two minutes of network and ~170 MB of
disk. In-room setup does not work: 40 laptops downloading at once will not finish in the
lab's 35 minutes.

## 1 · Install

```bash
pip install duckdb
```

Python 3.9+ and SQLite 3.25+ (both come with any current Python). No server, no Docker, no
admin rights.

## 2 · Build the data

```bash
python setup/build_data.py
```

This **generates** TPC-H at scale factor 0.1 locally using DuckDB's `tpch` extension and
exports the same rows into SQLite. Nothing large is downloaded; it takes a few seconds.

Expect roughly:

```
data/tpch.duckdb      30 MB     columnar
data/tpch.sqlite     137 MB     row-oriented, with B-tree indexes on every primary key
```

## 3 · Verify

```bash
python setup/verify_setup.py
```

It prints a line like:

```
WEEK1-SETUP 147790-148301-3774200-2  (duckdb 2.0.0, sqlite 3.41.2)
```

**Paste that line into the Canvas thread "Week 1 lab — setup check" before Friday.** Your
numbers should match exactly; the version numbers may differ.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: duckdb` | `pip install duckdb` — or `python -m pip install duckdb` if `pip` is not on your PATH |
| `pip` fails to build duckdb | You are on an old pip: `python -m pip install --upgrade pip`, then retry. DuckDB ships wheels for Windows, macOS (Intel + Apple Silicon) and Linux. |
| Extension download fails / you are offline | The `tpch` extension needs network **on first run only**. Run it once on a connected machine. |
| "SQLite is older than 3.25" | Upgrade Python. On Linux, your distro's `python3` may be linked against an old libsqlite3. |
| Row counts wrong, or verify fails | `rm -rf data` and re-run step 2. Never edit `data/` by hand. |
| Less than 4 GB of RAM, or very slow disk | `python setup/build_data.py --sf 0.01`. Every effect in the lab still shows, with smaller ratios — mention it in your write-up. |
| Out of disk | `--sf 0.01` builds in ~20 MB total. |
| Windows: `python` opens the Store | Use `py setup/build_data.py` |

If you are still stuck Thursday night, post in the Canvas thread with the **full error
text**. Do not wait until Friday — arriving without data costs you Task 4.

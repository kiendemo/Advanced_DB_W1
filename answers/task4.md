# Task 4 — Same SQL, two architectures

Machine: (CPU, cores, RAM, OS, on battery or plugged in?)
DuckDB version:        SQLite version:        Scale factor:

## 4a · The matrix

| Query | Guess: who wins? | DuckDB (ms) | SQLite (ms) | Speed-up | Winner |
|---|---|---|---|---|---|
| S1-scan-agg | | | | | |
| S2-scan-agg-filtered | | | | | |
| S3-one-column | | | | | |
| P1-point-order | | | | | |
| P2-point-customer | | | | | |

## 4b · Why one engine wins the scans

(two mechanisms — bytes read, and work per value — then the S3-vs-S1 check)

## 4c · Why the other wins the point lookups

(and: is DuckDB's missing index an oversight or a design choice?)

## 4d · The optimiser's mistake

Plan line for S2 in SQLite:
Why it is catastrophic at 98.5% selectivity:
Time with `NOT INDEXED`:            Factor recovered:
Why DuckDB barely changes:

## 4e · The covering index

Resolve the contradiction:
In what sense is a covering index a row store imitating a column store?

## 4f · Conclusion (<=150 words)

"Given a workload, I would choose a row store over a column store when ..., because ..."

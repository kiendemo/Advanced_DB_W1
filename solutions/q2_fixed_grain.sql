-- Task 2, Q2.3: lineitem is present, but orders are aggregated at their own grain
-- FIRST, so joining the finer-grained table cannot replicate order rows into SUM.
WITH order_lines AS (
    SELECT l_orderkey, COUNT(*) AS n_lines
    FROM   lineitem
    GROUP  BY l_orderkey
)
SELECT c.c_custkey,
       c.c_name,
       n.n_name,
       COUNT(*)              AS n_orders,
       SUM(o.o_totalprice)   AS total_value,
       SUM(ol.n_lines)       AS n_lines
FROM   customer c
       JOIN nation n   ON n.n_nationkey = c.c_nationkey
       JOIN orders o   ON o.o_custkey   = c.c_custkey
       JOIN order_lines ol ON ol.l_orderkey = o.o_orderkey
GROUP  BY c.c_custkey, c.c_name, n.n_name
HAVING COUNT(*) > 15
ORDER  BY total_value DESC, c.c_custkey ASC
LIMIT  10

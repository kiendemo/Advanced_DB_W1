-- Task 2: customers with more than 15 orders, top 10 by total order value.
-- GROUP BY carries every non-aggregated SELECT column; the c_custkey tie-break
-- makes the ORDER BY total, so LIMIT 10 is deterministic.
SELECT c.c_custkey,
       c.c_name,
       n.n_name,
       COUNT(*)              AS n_orders,
       SUM(o.o_totalprice)   AS total_value
FROM   customer c
       JOIN nation n ON n.n_nationkey = c.c_nationkey
       JOIN orders o ON o.o_custkey   = c.c_custkey
GROUP  BY c.c_custkey, c.c_name, n.n_name
HAVING COUNT(*) > 15
ORDER  BY total_value DESC, c.c_custkey ASC
LIMIT  10

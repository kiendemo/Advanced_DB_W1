-- Task 3(c)(iii): keep NOT IN, but guarantee the subquery is NULL-free.
-- Correct, but fragile: correctness depends on remembering this filter forever.
SELECT COUNT(*) AS not_held
FROM   orders o
WHERE  o.o_orderkey NOT IN (SELECT ho_orderkey
                            FROM   held_order
                            WHERE  ho_orderkey IS NOT NULL)

-- Task 3(b): one result that demonstrates the cause.
SELECT COUNT(*)                                        AS total_rows,
       COUNT(ho_orderkey)                              AS non_null_keys,
       COUNT(*) - COUNT(ho_orderkey)                   AS null_keys
FROM   held_order

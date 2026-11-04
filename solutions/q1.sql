-- Task 1: TPC-H Q1 (simplified). The date restriction belongs in WHERE: it is a
-- predicate on individual rows, so it must be applied BEFORE groups are formed.
SELECT l_returnflag,
       l_linestatus,
       COUNT(*)            AS cnt,
       SUM(l_quantity)     AS sum_qty,
       SUM(l_extendedprice) AS sum_price,
       AVG(l_discount)     AS avg_disc
FROM   lineitem
WHERE  l_shipdate <= '1998-09-01'
GROUP  BY l_returnflag, l_linestatus
ORDER  BY l_returnflag, l_linestatus

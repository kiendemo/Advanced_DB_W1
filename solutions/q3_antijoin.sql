-- Task 3(c)(ii): LEFT JOIN anti-join. Also robust: a NULL key never matches, so the
-- outer join keeps the order row and h.ho_orderkey IS NULL admits it.
-- NB: test IS NULL on the JOIN KEY, not on some other column of held_order.
SELECT COUNT(*) AS not_held
FROM   orders o
       LEFT JOIN held_order h ON h.ho_orderkey = o.o_orderkey
WHERE  h.ho_orderkey IS NULL

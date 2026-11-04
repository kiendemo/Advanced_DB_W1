-- Task 3(c)(i): NOT EXISTS. Robust BY CONSTRUCTION -- a NULL ho_orderkey simply
-- fails the correlation predicate, so it can never match and never suppresses a row.
-- This is the one to ship.
SELECT COUNT(*) AS not_held
FROM   orders o
WHERE  NOT EXISTS (SELECT 1
                   FROM   held_order h
                   WHERE  h.ho_orderkey = o.o_orderkey)

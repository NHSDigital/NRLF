INSERT INTO dimension.month (month, month_short_name, month_long_name)
VALUES
(1, 'Jan', 'January'),
(2, 'Feb', 'February'),
(3, 'Mar', 'March'),
(4, 'Apr', 'April'),
(5, 'May', 'May'),
(6, 'Jun', 'June'),
(7, 'Jul', 'July'),
(8, 'Aug', 'August'),
(9, 'Sep', 'September'),
(10, 'Oct', 'October'),
(11, 'Nov', 'November'),
(12, 'Dec', 'December')
ON CONFLICT (month) DO NOTHING;

INSERT INTO dimension.week (week)
VALUES
(1), (2), (3), (4), (5), (6), (7), (8), (9), (10),
(11), (12), (13), (14), (15), (16), (17), (18), (19), (20),
(21), (22), (23), (24), (25), (26), (27), (28), (29), (30),
(31), (32), (33), (34), (35), (36), (37), (38), (39), (40),
(41), (42), (43), (44), (45), (46), (47), (48), (49), (50),
(51), (52), (53)
ON CONFLICT (week) DO NOTHING;


INSERT INTO dimension.year (year)
VALUES
(2021), (2022), (2023), (2024), (2025), (2026), (2027),
(2028), (2029), (2030), (2031), (2032), (2033), (2034),
(2035), (2036), (2037), (2038), (2039), (2040)
ON CONFLICT (year) DO NOTHING;


INSERT INTO dimension.day_of_week (day_of_week, short_name, long_name)
VALUES
(0, 'Sun', 'Sunday'),
(1, 'Mon', 'Monday'),
(2, 'Tue', 'Tuesday'),
(3, 'Wed', 'Wednesday'),
(4, 'Thu', 'Thursday'),
(5, 'Fri', 'Friday'),
(6, 'Sat', 'Saturday')
ON CONFLICT (day_of_week) DO NOTHING;

INSERT INTO dimension.day (day)
VALUES
(1), (2), (3), (4), (5), (6), (7), (8), (9), (10),
(11), (12), (13), (14), (15), (16), (17), (18), (19), (20),
(21), (22), (23), (24), (25), (26), (27), (28), (29), (30),
(31)
ON CONFLICT (day) DO NOTHING;

INSERT INTO dimension.status (status_id, status_name)
VALUES
(0, 'deleted'),
(1, 'active')
ON CONFLICT (status_id) DO NOTHING;

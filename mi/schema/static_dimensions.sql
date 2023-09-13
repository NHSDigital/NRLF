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

INSERT INTO dimension.year (year)
VALUES
(2021), (2022), (2023), (2024), (2025), (2026), (2027),
(2028), (2029), (2030), (2031), (2032), (2033), (2034),
(2035), (2036), (2037), (2038), (2039), (2040),
(2041), (2042), (2043), (2044), (2045), (2046), (2047),
(2048), (2049), (2050), (2051), (2052), (2053), (2054),
(2055), (2056), (2057), (2058), (2059), (2060), (2061),
(2062), (2063), (2064), (2065), (2066), (2067), (2068),
(2069), (2070), (2071), (2072), (2073), (2074), (2075),
(2076), (2077), (2078), (2079), (2080), (2081), (2082),
(2083), (2084), (2085), (2086), (2087), (2088), (2089),
(2090), (2091), (2092), (2093), (2094), (2095), (2096),
(2097), (2098), (2099), (2100), (2101)
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

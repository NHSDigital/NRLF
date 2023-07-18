SELECT
    MIN(dimension.producer.producer_name) AS producer_name,
    MIN(dimension.month.month_short_name) AS month,
    fact.measure.year AS year,
    SUM(fact.measure.count) AS count
FROM fact.measure
INNER JOIN
    dimension.producer
    ON fact.measure.producer_id = dimension.producer.producer_id
INNER JOIN dimension.month ON fact.measure.month = dimension.month.month
INNER JOIN dimension.year ON fact.measure.year = dimension.year.year
WHERE fact.measure.partition_key = %(partition_key)s
GROUP BY fact.measure.producer_id, fact.measure.month, fact.measure.year
ORDER BY
    producer_name ASC, fact.measure.year ASC, fact.measure.month ASC, count DESC;

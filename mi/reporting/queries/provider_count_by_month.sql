SELECT
    MIN(dimension.provider.provider_name) AS provider_name,
    MIN(dimension.month.month_short_name) AS month,
    fact.measure.year AS year,
    SUM(fact.measure.count_created) AS count
FROM fact.measure
INNER JOIN
    dimension.provider
    ON fact.measure.provider_id = dimension.provider.provider_id
INNER JOIN dimension.month ON fact.measure.month = dimension.month.month
INNER JOIN dimension.year ON fact.measure.year = dimension.year.year
WHERE fact.measure.partition_key = %(partition_key)s
GROUP BY fact.measure.provider_id, fact.measure.month, fact.measure.year
ORDER BY
    provider_name ASC, fact.measure.year ASC, fact.measure.month ASC, count DESC;

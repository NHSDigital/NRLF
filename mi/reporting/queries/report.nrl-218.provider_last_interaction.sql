SELECT
    MIN(dimension.provider.provider_name) AS provider_name,
    TO_CHAR(MAX(DATE(fact.measure.year || '-' || fact.measure.month || '-' || fact.measure.day)), 'YYYY-MM-DD') AS last_interaction_date,
    (CASE WHEN (fact.measure.count_deleted = 0) THEN 'CREATE' ELSE 'DELETE' END) AS interaction_type
FROM fact.measure
INNER JOIN
    dimension.provider
    ON fact.measure.provider_id = dimension.provider.provider_id
WHERE
    fact.measure.partition_key = %(partition_key)s
GROUP BY fact.measure.provider_id, interaction_type
ORDER BY
    last_interaction_date DESC, provider_name ASC, interaction_type ASC;

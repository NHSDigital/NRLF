SELECT
    MIN(dimension.provider.provider_name) AS provider_name,
    ARRAY_AGG(DISTINCT dimension.document_type.document_type_system || '|' || dimension.document_type.document_type_code) AS list_pointer_types,
    COUNT(*) as count
FROM fact.measure
INNER JOIN
    dimension.provider
    ON fact.measure.provider_id = dimension.provider.provider_id
INNER JOIN
    dimension.document_type
    ON fact.measure.document_type_id = dimension.document_type.document_type_id
WHERE
    fact.measure.partition_key = %(partition_key)s
    AND fact.measure.count_created > 0
    AND fact.measure.count_deleted = 0
    AND DATE(year || '-' || month || '-' || day) BETWEEN  %(start_date)s AND  %(end_date)s
GROUP BY fact.measure.provider_id
ORDER BY
    provider_name ASC, count DESC;

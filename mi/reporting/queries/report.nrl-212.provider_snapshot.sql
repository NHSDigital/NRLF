SELECT
    MIN(dimension.provider.provider_name) AS provider_name,
    MIN(dimension.document_type.document_type_system) AS system,
    MIN(dimension.document_type.document_type_code) AS type,
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
GROUP BY fact.measure.provider_id, fact.measure.document_type_id
ORDER BY
    count DESC, provider_name ASC, system ASC, type ASC;

INSERT INTO dimension.document_type
(
    document_type_code,
    document_type_system
)
VALUES (
   %(document_type_code)s,
   %(document_type_system)s
)
ON CONFLICT (document_type_code, document_type_system) DO NOTHING

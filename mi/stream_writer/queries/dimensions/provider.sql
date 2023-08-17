INSERT INTO dimension.provider
(
    provider_name
)
VALUES (
   %(provider_name)s
)
ON CONFLICT (provider_name) DO NOTHING

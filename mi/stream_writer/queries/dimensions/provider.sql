INSERT INTO dimension.provider
(
    provider_name,
    provider_suffix
)
VALUES (
   %(provider_name)s,
   %(provider_suffix)s
)
ON CONFLICT (provider_name, provider_suffix) DO NOTHING

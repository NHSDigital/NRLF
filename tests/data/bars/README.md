# BaRS data

1. `1_bars_sample_original.json`

   is the document submitted to us by BaRS

1. `2_bars_sample_fhir_compliant.json`

   is the cut down version of the original that can be accepted by the current API.

1. `3_bars_sample_accepted.json`

   is the version the api accepted, which had to remove the `relatesTo` because those documents didn't exist in our system.

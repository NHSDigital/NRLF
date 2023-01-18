resource "aws_ssm_parameter" "apigee_proxy" {
  name        = "/${local.prefix}/apigee-proxy"
  description = "APIGEE Proxy for the Environment.  Set to Whitespace to disable Smoke Tests."
  type        = "String"
  value       = " " # Making this value a blank value will skip the Smoke Test
}

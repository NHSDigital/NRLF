resource "aws_secretsmanager_secret" "splunk_configuration" {
  name        = "${var.prefix}--splunk-hec-configuration"
  description = "HEC URL/Token for forwarding logs to Splunk. 'none' means no forwarding."
}

data "aws_secretsmanager_secret_version" "splunk_configuration" {
  # Note that this secret should have a value which is a JSON string
  # according to the following template:
  #
  # {
  #   "nhs_splunk_url": "mysplunkserver.example.com:8088",
  #   "hec_token": "12345"
  # }
  #
  count     = var.destination == "splunk" ? 1 : 0
  secret_id = aws_secretsmanager_secret.splunk_configuration.name
}

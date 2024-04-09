data "aws_secretsmanager_secret_version" "splunk_configuration" {
  # Note that this secret should have a value which is a JSON string
  # according to the following template:
  #
  # {
  #   "nhs_splunk_url": "mysplunkserver.example.com:8088",
  #   "hec_token": "12345"
  # }
  #
  secret_id = "nhsd-nrlf--${var.splunk_environment}--splunk-configuration"
}

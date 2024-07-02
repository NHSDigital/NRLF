resource "aws_api_gateway_domain_name" "domain" {
  domain_name              = aws_acm_certificate.certificate.domain_name
  regional_certificate_arn = aws_acm_certificate.certificate.arn
  security_policy          = "TLS_1_2"
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  mutual_tls_authentication {
    truststore_uri = var.mtls_certificate_file
  }

  depends_on = [
    aws_acm_certificate_validation.validation
  ]
}

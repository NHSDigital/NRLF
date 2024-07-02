
module "dev-custom-domain-name" {
  source                    = "../modules/env-custom-domain-name"
  domain_name               = var.dev_api_domain_name
  domain_zone               = aws_route53_zone.NEW_dev-ns.name
  subject_alternative_names = [aws_route53_zone.NEW_dev-ns.name]
  mtls_certificate_file     = "s3://${module.dev-truststore-bucket.bucket_name}/${module.dev-truststore-bucket.certificates_object_key}"
}

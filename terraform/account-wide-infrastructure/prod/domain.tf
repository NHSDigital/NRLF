
module "dev-custom-domain-name" {
  source                    = "../modules/env-custom-domain-name"
  domain_name               = var.prod_api_domain_name
  domain_zone               = aws_route53_zone.prod-ns.name
  subject_alternative_names = [aws_route53_zone.prod-ns.name]
  mtls_certificate_file     = "s3://${module.prod-truststore-bucket.bucket_name}/${module.prod-truststore-bucket.certificates_object_key}"
}

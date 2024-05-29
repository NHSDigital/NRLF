resource "aws_route53_zone" "dev-ns" {
  name = "api.record-locator.dev.national.nhs.uk"
}

resource "aws_route53_zone" "NEW_dev-ns" {
  name = "dev.record-locator.national.nhs.uk"
}

resource "aws_route53_zone" "test-qa-ns" {
  name = "api.record-locator.qa.national.nhs.uk"
}

resource "aws_route53_zone" "test-int-ns" {
  name = "api.record-locator.int.national.nhs.uk"
}

resource "aws_route53_zone" "test-ref-ns" {
  name = "api.record-locator.ref.national.nhs.uk"
}

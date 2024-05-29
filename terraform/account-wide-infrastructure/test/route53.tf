resource "aws_route53_zone" "test-qa-ns" {
  name = "qa.record-locator.national.nhs.uk"
}

resource "aws_route53_zone" "NEW_test-int-ns" {
  name = "int.record-locator.national.nhs.uk"
}

resource "aws_route53_zone" "test-int-ns" {
  name = "api.record-locator.int.national.nhs.uk"
}

resource "aws_route53_zone" "NEW_test-ref-ns" {
  name = "ref.record-locator.national.nhs.uk"
}

resource "aws_route53_zone" "test-ref-ns" {
  name = "api.record-locator.ref.national.nhs.uk"
}

resource "aws_route53_zone" "test-ns" {
  name = "api.record-locator.ref.national.nhs.uk"
}

resource "aws_route53_zone" "test-int-ns" {
  name = "api.record-locator.int.national.nhs.uk"
}

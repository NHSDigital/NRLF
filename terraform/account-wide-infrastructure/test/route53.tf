// TODO-NOW - Make sure this zone is created and delegated to us
resource "aws_route53_zone" "test-ns" {
  name = "api.record-locator.test.national.nhs.uk"
}

resource "aws_route53_zone" "test-int-ns" {
  name = "api.record-locator.int.national.nhs.uk"
}

resource "aws_route53_zone" "test-ref-ns" {
  name = "api.record-locator.ref.national.nhs.uk"
}

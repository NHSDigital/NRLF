resource "aws_route53_zone" "prod_zone" {
  name = "record-locator.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "prodspine" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "prod.internal.record-locator.spineservices.nhs.uk"
  records = ["ns-904.awsdns-49.net.",
    "ns-1539.awsdns-00.co.uk.",
    "ns-1398.awsdns-46.org.",
    "ns-300.awsdns-37.com."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "ref_zone" {
  name = "record-locator.ref.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "refspine" {
  zone_id = aws_route53_zone.ref_zone.zone_id
  name    = "test.internal.record-locator.refspineservices.nhs.uk"
  records = ["ns-397.awsdns-49.com.",
    "ns-880.awsdns-46.net.",
    "ns-1660.awsdns-15.co.uk.",
    "ns-1446.awsdns-52.org."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "dev_zone" {
  name = "record-locator.dev.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "devspine" {
  zone_id = aws_route53_zone.dev_zone.zone_id
  name    = "dev.internal.record-locator.devspineservices.nhs.uk"
  records = ["ns-1184.awsdns-20.org.",
    "ns-658.awsdns-18.net.",
    "ns-1591.awsdns-06.co.uk.",
    "ns-304.awsdns-38.com."
  ]
  ttl  = 300
  type = "NS"
}

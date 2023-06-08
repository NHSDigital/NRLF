resource "aws_iam_role" "rds-cluster-ref" {
  name        = "nhsd-nrlf-ref-rds-cluster"
  description = "Role for RDS cluster"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action : "sts:AssumeRole",
        Principal : { Service : "rds.amazonaws.com" },
        Effect : "Allow",
        Sid : ""
      }
    ]
  })
}
resource "aws_iam_role" "rds-cluster-int" {
  name        = "nhsd-nrlf-int-rds-cluster"
  description = "Role for RDS cluster"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action : "sts:AssumeRole",
        Principal : { Service : "rds.amazonaws.com" },
        Effect : "Allow",
        Sid : ""
      }
    ]
  })
}

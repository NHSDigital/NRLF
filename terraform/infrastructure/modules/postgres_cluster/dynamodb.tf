resource "aws_lambda_event_source_mapping" "dynamodb-stream-source" {
  event_source_arn  = var.dynamodb_table.stream_arn
  function_name     = module.rds-cluster-stream-writer.arn
  starting_position = "LATEST"
}

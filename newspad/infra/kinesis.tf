resource "aws_kinesis_stream" "guardian_stream" {
  name             = "guardian-content-stream"
  shard_count      = 1
  retention_period = 24

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

resource "aws_iam_policy" "kinesis_write_policy" {
  name = "lambda_kinesis_write_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords"
        ]
        Effect   = "Allow"
        Resource = aws_kinesis_stream.guardian_stream.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_kinesis_write_attachment" {
  role       = aws_iam_role.role_for_producer_lambda.name
  policy_arn = aws_iam_policy.kinesis_write_policy.arn
}

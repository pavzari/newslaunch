resource "aws_kinesis_stream" "guardian_stream" {
  name             = "guardian_content"
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


resource "aws_iam_policy" "kinesis_consumer_lambda_policy" {
  name = "consumer_lambda_kinesis_policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "kinesis:DescribeStream",
          "kinesis:DescribeStreamSummary",
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:ListShards",
          "kinesis:ListStreams",
          "kinesis:SubscribeToShard",
        ],
        "Resource" : "${aws_kinesis_stream.guardian_stream.arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "producer_lambda_kinesis_policy_attachment" {
  role       = aws_iam_role.role_for_consumer_lambda.name
  policy_arn = aws_iam_policy.kinesis_consumer_lambda_policy.arn
}

resource "aws_lambda_event_source_mapping" "kinesis_consumer_lambda_mapping" {
    # batch_size = ...
  event_source_arn  = aws_kinesis_stream.guardian_stream.arn
  function_name     = aws_lambda_function.consumer_lambda.arn
  starting_position = "LATEST"
}

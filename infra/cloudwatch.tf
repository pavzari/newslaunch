resource "aws_iam_policy" "cloudwatch_logs_policy" {
  name = "lambda_cloudwatch_logs_policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "logs:CreateLogGroup",
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action   = "logs:CreateLogStream",
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action   = "logs:PutLogEvents",
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_cw_write_attachment" {
  role       = aws_iam_role.role_for_producer_lambda.name
  policy_arn = aws_iam_policy.cloudwatch_logs_policy.arn
}


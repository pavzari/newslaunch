resource "aws_s3_bucket" "lambda_code_bucket" {
  bucket_prefix = "streamlaunch-lambda-code-bucket-"
}

data "archive_file" "producer_lambda_code_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../streamlaunch"
  output_path = "${path.module}/../streamlaunch/producer_lambda.zip"
}

resource "aws_s3_object" "producer_lambda_code_upload" {
  bucket      = aws_s3_bucket.lambda_code_bucket.id
  key         = "producer_lambda.zip"
  source      = data.archive_file.producer_lambda_code_zip.output_path
  source_hash = filemd5(data.archive_file.producer_lambda_code_zip.output_path)
}

resource "null_resource" "install_layer_dep" {
  provisioner "local-exec" {
    command = "pip install -r producer_layer/requirements.txt -t producer_layer/python/lib/python3.11/site-packages"
  }
  triggers = {
    trigger = filemd5("producer_layer/requirements.txt")
  }
}

data "archive_file" "producer_layer_zip" {
  type        = "zip"
  source_dir  = "producer_layer"
  output_path = "producer_layer.zip"
  depends_on = [
    null_resource.install_layer_dep
  ]
}

resource "aws_lambda_layer_version" "producer_lambda_layer" {
  filename            = "producer_layer.zip"
  source_code_hash    = data.archive_file.producer_layer_zip.output_base64sha256
  layer_name          = "producer_layer"
  compatible_runtimes = ["python3.11"]
  depends_on = [
    data.archive_file.producer_layer_zip
  ]
}

variable "guardian_api_key" {
type      = string
sensitive = true
}

resource "aws_lambda_function" "producer_lambda" {
  function_name    = "producer_lambda"
  handler          = "producer_lambda.lambda_handler"
  runtime          = "python3.11"
  timeout          = 100
  role             = aws_iam_role.role_for_producer_lambda.arn
  s3_bucket        = aws_s3_bucket.lambda_code_bucket.id
  s3_key           = "producer_lambda.zip"
  layers           = [aws_lambda_layer_version.producer_lambda_layer.arn]
  source_code_hash = resource.aws_s3_object.producer_lambda_code_upload.source_hash

  environment {
    variables = {
      GUARDIAN_API_KEY = var.guardian_api_key
    }
  }
}

resource "aws_iam_role" "role_for_producer_lambda" {
  name = "role_for_producer_lambda"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "sts:AssumeRole"
        ],
        "Principal" : {
          "Service" : [
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })
}



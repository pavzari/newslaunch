data "archive_file" "consumer_lambda_code_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/consumer.py"
  output_path = "${path.module}/../lambda/consumer_lambda.zip"
}

resource "aws_s3_object" "consumer_lambda_code_upload" {
  bucket      = aws_s3_bucket.lambda_code_bucket.id
  key         = "consumer_lambda.zip"
  source      = data.archive_file.consumer_lambda_code_zip.output_path
  source_hash = filemd5(data.archive_file.consumer_lambda_code_zip.output_path)
}

# resource "null_resource" "install_layer_consumer" {
#   provisioner "local-exec" {
#     command = "pip install -r producer_layer/requirements.txt -t producer_layer/python/lib/python3.11/site-packages"
#   }
#   triggers = {
#     trigger = filemd5("producer_layer/requirements.txt")
#   }
# }
# 
# data "archive_file" "consumer_layer_zip" {
#   type        = "zip"
#   source_dir  = "consumer_layer"
#   output_path = "consumer_layer.zip"
#   depends_on = [
#     null_resource.install_layer_consumer
#   ]
# }
# 
# resource "aws_lambda_layer_version" "consumer_lambda_layer" {
#   filename            = "consumer_layer.zip"
#   source_code_hash    = data.archive_file.consumer_layer_zip.output_base64sha256
#   layer_name          = "consumer_layer"
#   compatible_runtimes = ["python3.11"]
#   depends_on = [
#     data.archive_file.consumer_layer_zip
#   ]
# }

resource "aws_lambda_function" "consumer_lambda" {
  function_name = "consumer"
  handler       = "consumer.lambda_handler"
  runtime       = "python3.11"
  timeout       = 100
  role          = aws_iam_role.role_for_consumer_lambda.arn
  s3_bucket     = aws_s3_bucket.lambda_code_bucket.id
  s3_key        = "consumer_lambda.zip"
  # layers           = [aws_lambda_layer_version.consumer_lambda_layer.arn]
  source_code_hash = resource.aws_s3_object.consumer_lambda_code_upload.source_hash
}

resource "aws_iam_role" "role_for_consumer_lambda" {
  name = "role_for_consumer_lambda"
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



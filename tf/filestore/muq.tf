resource "aws_sqs_queue" "muq" {
    name = var.MUQ_NAME[terraform.workspace]

    visibility_timeout_seconds = var.MUQ_VT[terraform.workspace]
    message_retention_seconds = var.MUQ_MR[terraform.workspace]
    receive_wait_time_seconds = var.MUQ_RW[terraform.workspace]

    tags = {
      Name = "${var.SERVICE_PREFIX[terraform.workspace]}-muq"
    }
}

resource "aws_sqs_queue_policy" "mb_to_muq" {
  queue_url = aws_sqs_queue.muq.id
  policy = data.aws_iam_policy_document.mb_to_muq.json
}

resource "aws_s3_bucket_notification" "mb_to_muq" {
  bucket = data.aws_s3_bucket.mb.id

  queue {
    queue_arn = aws_sqs_queue.muq.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix = var.MB_INPUT_PREFIX[terraform.workspace]
  }
}
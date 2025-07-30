data "aws_caller_identity" "current" {}

data "aws_route53_zone" "root" {
  name = var.ROOT_FQDN[terraform.workspace]
}

data "aws_acm_certificate" "wildcard" {
  domain = "*.${var.ROOT_FQDN[terraform.workspace]}"
  statuses = [ "ISSUED" ]

  provider = aws.virginia
}

data "aws_s3_bucket" "mb" {
  bucket = var.MB_NAME[terraform.workspace]
}

data "aws_iam_policy_document" "mcf_to_mb" {
  statement {
    actions = [ "S3:GetObject" ]
    resources = [ "${data.aws_s3_bucket.mb.arn}/*" ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test = "ArnEquals"
      variable = "AWS:SourceArn"
      values = [ aws_cloudfront_distribution.mcf.arn ]
    }
  }
}

data "aws_iam_policy_document" "mb_to_muq" {
    statement {
    actions   = [ "sqs:SendMessage" ]
    resources = [ aws_sqs_queue.muq.arn ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "AWS:SourceArn"
      values   = [ data.aws_s3_bucket.mb.arn ]
    }
  }
}
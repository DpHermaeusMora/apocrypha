resource "aws_ecr_repository" "api_server" {  
  name                 = var.API_SERVER_IMAGE_NAME[terraform.workspace]
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    "Name" = "${var.SERVICE_PREFIX[terraform.workspace]}_ecr_api_server"
  }
}

resource "aws_ecr_lifecycle_policy" "api_server" {  
  repository = aws_ecr_repository.api_server.name
  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 3 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 3
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}
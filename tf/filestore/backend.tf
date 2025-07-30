terraform {
  backend "s3" {
    workspace_key_prefix = "tf/filestore/env:"
    key = "terraform.tfstate"
    region = "ap-northeast-2"
    bucket = "apocrypha-secret"
  }
}
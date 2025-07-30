provider "aws" {
  shared_config_files = [ "~/.aws/config" ]
  shared_credentials_files = [ "~/.aws/credentials" ]
  profile = var.AWS_PROFILE[terraform.workspace]
  region = var.AWS_REGION[terraform.workspace]
}

provider "aws" {
  shared_config_files = [ "~/.aws/config" ]
  shared_credentials_files = [ "~/.aws/credentials" ]
  profile = var.AWS_PROFILE[terraform.workspace]
  region = "us-east-1"
  alias = "virginia"
}

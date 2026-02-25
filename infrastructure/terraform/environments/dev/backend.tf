terraform {
  backend "s3" {
    bucket         = "imagineai-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "imagineai-terraform-locks"
    encrypt        = true
  }
}

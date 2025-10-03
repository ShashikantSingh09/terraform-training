terraform {
  backend "s3" {
    bucket  = "my-terraform-state-bucket-afrotech-new-2"
    key     = "state/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
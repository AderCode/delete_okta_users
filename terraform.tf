# Specify the provider and its configuration
provider "aws" {
  region = var.AWS_REGION # Replace with your desired AWS region
}

# Create an S3 bucket
resource "aws_s3_bucket" "my_bucket" {
  bucket = var.TARGET_BUCKET # Replace with your desired bucket name
  acl    = "private"         # Set the bucket access control list (ACL)
}

# Create default folder in the bucket
resource "aws_s3_bucket_object" "default_folder_structure" {
  bucket = aws_s3_bucket.my_bucket.bucket
  key    = "${var.KEY_PREFIX}/${var.JOB_NAME}/data/input/okta_emails/"
  acl    = "private"
}

# Create default folder in the bucket
resource "aws_s3_bucket_object" "default_folder_structure2" {
  bucket = aws_s3_bucket.my_bucket.bucket
  key    = "${var.KEY_PREFIX}/${var.JOB_NAME}/data/input/okta_ids/"
  acl    = "private"
}

# Define variables
variable "AWS_REGION" {
  description = "The AWS region"
  type        = string
}

variable "TARGET_BUCKET" {
  description = "The target S3 bucket name"
  type        = string
}

variable "KEY_PREFIX" {
  description = "The key prefix for the S3 bucket objects"
  type        = string
}

variable "JOB_NAME" {
  description = "The job name"
  type        = string
}
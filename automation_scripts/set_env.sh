#!/bin/bash
# Create the Terraform variables file
cat <<EOF > terraform.tfvars
AWS_REGION = "$AWS_DEFAULT_REGION"
TARGET_BUCKET = "$TARGET_S3_BUCKET"
JOB_NAME = "$JOB_NAME"
KEY_PREFIX = "$S3_PREFIX"
ENVIRONMENT = "$ENVIRONMENT"
EOF
"""Module to interact with S3"""

import boto3
from .env_util import Env
from .logging_util import Logger


class S3Util:
    """Class to interact with S3"""

    def __init__(self):
        self.bucket = Env.get("TARGET_S3_BUCKET")
        self.client = boto3.client("s3")
        self.prefix = f"{Env.get('S3_PREFIX', '.').strip('/')}/{Env.get('JOB_NAME')}"
        self.log = Logger("s3_util.py")

    def get_object(self, key):
        """Function to get object from S3"""
        s3_key = f"{self.prefix}/{key}"
        response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
        return response["Body"].read().decode("utf-8")

    def put_object(self, key, data):
        """Function to upload object to S3"""
        s3_key = f"{self.prefix}/{key}"
        response = self.client.put_object(Bucket=self.bucket, Key=s3_key, Body=data)
        return response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def download_file(self, key, filename):
        """Function to download file from S3"""
        s3_key = f"{self.prefix}/{key}"
        self.log.info(f"Downloading file from S3: {s3_key} to {filename}")
        self.client.download_file(str(self.bucket), str(s3_key), str(filename))
        self.log.info(f"Downloaded file: {filename}")

    def upload_fileobj(self, key, fileobj):
        """Function to upload file to S3"""
        s3_key = f"{self.prefix}/{key}"
        self.log.info(f"Uploading file to S3: {s3_key}")
        try:
            self.client.upload_fileobj(fileobj, self.bucket, s3_key)
            self.log.info(f"Uploaded file to S3: {s3_key}")
        except Exception as e:
            self.log.error(f"Failed to upload file to S3: {s3_key}")
            self.log.error(str(e))

    def delete_object(self, key):
        """Function to delete object from S3"""
        s3_key = f"{self.prefix}/{key}"
        response = self.client.delete_object(Bucket=self.bucket, Key=s3_key)
        status_code = response["ResponseMetadata"].get("HTTPStatusCode")
        if status_code:
            return status_code == 204

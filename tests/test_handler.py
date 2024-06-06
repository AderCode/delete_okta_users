import pytest
import boto3
from os import environ
from moto import mock_aws

@pytest.fixture
def mock_s3():
    """Mock S3 bucket"""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=environ.get("TARGET_S3_BUCKET"))
        with open("./tests/files/test_ids.csv", "rb") as data:
            s3.upload_fileobj(
                Bucket=environ.get("TARGET_S3_BUCKET"),
                Key=f"{environ.get('S3_PREFIX')}/{environ.get('JOB_NAME')}/data/input/test_ids.csv",
                Fileobj=data,
            )
        yield s3

@mock_aws
def test_main(mock_s3):
    from src.app.main import main

    try:
        main()
        assert True
    except Exception as e:
        assert False, e

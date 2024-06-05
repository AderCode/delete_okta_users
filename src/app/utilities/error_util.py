import csv
from .s3_util import S3Util
from .env_util import Env

s3 = S3Util()


def record_failed_attempt(okta_id: str, path: str) -> None:
    """Function to record failed attempts into a CSV file"""
    s3_enabled = bool(Env.get("TARGET_S3_BUCKET"))

    with open("../" + path, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([okta_id])

    if s3_enabled:
        with open(f"../{path}", "rb") as data:
            s3.upload_fileobj(path, data)

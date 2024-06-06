# Author: Matthew Aderhold (AderCode)
""" This script reads a CSV file with Okta IDs and deactivates then deletes the users. """

# pylint: disable= C0301, W0718, C0103, C0411, W0621, W0612

import os
import csv
import importlib.util

from .utilities.okta_util import Okta
from .utilities.logging_util import Logger
from .utilities.env_util import Env
from .utilities.s3_util import S3Util
from .utilities.config_util import CONFIG
from .utilities.reporting_util import ReportingUtil
from .utilities.error_util import record_failed_attempt
LOG = Logger("main.py")

# Main function to process the CSV and delete users
def main():
    """Main function to process the CSV and delete users"""
    reporting = ReportingUtil()
    reporting.start()

    # Check if S3 is enabled
    s3_enabled = bool(Env.get("TARGET_S3_BUCKET"))
    if s3_enabled:
        s3 = S3Util()

    input_csv_path = CONFIG["INPUT_CSV_PATH"]

    # If S3 is enabled check for a input csv file and download it
    if s3_enabled:
        try:
            s3.download_file(input_csv_path, f"{CONFIG['SRC_PATH']}{input_csv_path}")
        except Exception as e:
            LOG.error("Error downloading input CSV file from S3: " + str(e))

    # Check file exists
    LOG.info("Checking if input CSV file exists: " + input_csv_path)
    try:
        with open(CONFIG["SRC_PATH"] + input_csv_path, mode="r", encoding="utf-8-sig") as csv_file:
            pass
    except FileNotFoundError:
        LOG.error("Input CSV file not found: " + input_csv_path)
        return

    # First, determine the total number of rows in the CSV
    with open(CONFIG["SRC_PATH"] + input_csv_path, mode="r", encoding="utf-8-sig") as csv_file:
        total_rows = sum(
            1 for row in csv.reader(csv_file)
        )  # Count the number of rows in the CSV file
        LOG.info("Total rows in input CSV: " + str(total_rows) + "\n")
        CONFIG["TOTAL_ROWS"] = total_rows

    okta = Okta()
    
    # Process the CSV file
    with open(CONFIG["SRC_PATH"] + input_csv_path, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.reader(csv_file)
        current_row = 0  # Initialize current row counter

        for row in csv_reader:
            current_row += 1
            okta_id = str(row[0])

            # Calculate the percentage of completion
            percentage_done = (current_row / total_rows) * 100

            # Print current row number, Okta ID, and percentage done
            LOG.info(f"Processing row {current_row}/{total_rows}")
            LOG.info("Current Okta ID: " + okta_id)

            step = 0

            try:
                user_response = okta.get_user(okta_id)  # Check if the user exists
                if user_response["status_code"] == 404:
                    # If the user is already not in Okta, move on.
                    LOG.info(f"User {okta_id} not found in Okta")

                elif user_response["status_code"] == 200:
                    user = user_response.json
                    # If the user is already deactivated, then move on to deleting them
                    if user["status"] == "DEPROVISIONED":
                        step = 2
                    else:
                        step = 1

                if step == 1:
                    deactivate_successful = okta.deactivate_user(
                        okta_id
                    )  # Deactivate then delete the user
                    if deactivate_successful:
                        CONFIG["TOTAL_USERS_DEACTIVATED"] += 1
                        step = 2

                if step == 2:
                    okta.delete_user(okta_id)
                    CONFIG["TOTAL_USERS_DELETED"] += 1

            except Exception as e:
                LOG.error("Error processing Okta ID " + okta_id + f": {e}")
                
                failed_attempt_csv_path = None
                if step == 1:
                    CONFIG["DEACTIVATION_ERROR_COUNT"] += 1
                    failed_attempt_csv_path = CONFIG["FAILED_FIRST_CALL_CSV_PATH"]
                elif step == 2:
                    CONFIG["DELETE_ERROR_COUNT"] += 1
                    failed_attempt_csv_path = CONFIG["FAILED_SECOND_CALL_CSV_PATH"]

                if failed_attempt_csv_path is not None:
                    record_failed_attempt(okta_id, failed_attempt_csv_path)

            LOG.info(f"Progress: ~{percentage_done:.2f}% done\n")
            CONFIG["TOTAL_ROWS_PROCESSED"] = current_row

    reporting.finish()
    reporting.generate()

    # If S3 is enabled, upload the log file
    if s3_enabled:
        s3_path = f"{CONFIG['LOG_FILE_PATH']}"
        local_log_file_path = f"{CONFIG['SRC_PATH']}{s3_path}"
        with open(local_log_file_path, "rb") as data:
            s3.upload_fileobj(s3_path, data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        LOG.error("An error occurred: " + str(e))
        raise e


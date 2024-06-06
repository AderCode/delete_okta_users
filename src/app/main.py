# Author: Matthew Aderhold (AderCode)
""" This script reads a CSV file with Okta IDs and deactivates then deletes the users. """

# pylint: disable= C0301, W0718, C0103, C0411, W0621, W0612

import csv

from .utilities.okta_util import Okta
from .utilities.logging_util import Logger
from .utilities.env_util import Env
from .utilities.s3_util import S3Util
from .utilities.config_util import CONFIG
from .utilities.reporting_util import ReportingUtil
from .utilities.error_util import record_failed_attempt

LOG = Logger("main.py")

SRC_PATH = CONFIG["SRC_PATH"]
INPUT_IDS_CSV_PATH = CONFIG["INPUT_IDS_CSV_PATH"]
INPUT_EMAILS_CSV_PATH = CONFIG["INPUT_EMAILS_CSV_PATH"]


def check_total_rows(path: str) -> None:
    """Function to check the total number of rows in the input CSV file"""
    with open(SRC_PATH + path, mode="r", encoding="utf-8-sig") as csv_file:
        total_rows = sum(
            1 for row in csv.reader(csv_file)
        )  # Count the number of rows in the CSV file
        LOG.info("Total rows in input CSV: " + str(total_rows) + "\n")
        CONFIG["TOTAL_ROWS"] = total_rows
        return total_rows


def check_for_file() -> None:
    """Function to check if a file exists"""
    try:
        LOG.info("Checking if input CSV file exists: " + INPUT_IDS_CSV_PATH)
        with open(
            SRC_PATH + INPUT_IDS_CSV_PATH, mode="r", encoding="utf-8-sig"
        ) as csv_file:
            pass
        return "ids"
    except FileNotFoundError:
        LOG.error("Input CSV file not found: " + INPUT_IDS_CSV_PATH)
        try:
            LOG.info(
                "Checking if input Emails CSV file exists: " + INPUT_EMAILS_CSV_PATH
            )
            with open(
                SRC_PATH + INPUT_EMAILS_CSV_PATH, mode="r", encoding="utf-8-sig"
            ) as csv_file:
                pass
            return "emails"
        except Exception as e:
            LOG.error(e)
            LOG.error("Input CSV files not found. Exiting.")
            return None


def download_data_files(s3: S3Util) -> None:
    """Function to download the input CSV files from S3"""
    try:
        s3.download_file(INPUT_IDS_CSV_PATH, f"{SRC_PATH}{INPUT_IDS_CSV_PATH}")
        return "ids"
    except Exception as e:
        LOG.error("Error downloading input Okta IDs CSV file from S3: " + str(e))
        try:
            s3.download_file(
                INPUT_EMAILS_CSV_PATH, f"{SRC_PATH}{INPUT_EMAILS_CSV_PATH}"
            )
            return "emails"
        except Exception as e:
            LOG.error("Error downloading input Okta Emails CSV file from S3: " + str(e))


def upload_logs_to_s3(s3: S3Util, log_file_path: str) -> None:
    """Function to upload the log file to S3"""
    local_log_file_path = f"{SRC_PATH}{log_file_path}"
    with open(local_log_file_path, "rb") as data:
        s3.upload_fileobj(log_file_path, data)


def delete_deprovisioned_user(okta: Okta, user_id: str):
    """Function to delete a deprovisioned user"""
    LOG.debug("[MOCK] Deleting deprovisioned user with ID: " + user_id)
    try:
        # okta.delete_user(user_id)
        CONFIG["TOTAL_USERS_DELETED"] += 1
    except Exception as err:
        CONFIG["DELETE_ERROR_COUNT"] += 1
        record_failed_attempt(user_id, CONFIG["FAILED_SECOND_CALL_CSV_PATH"])
        raise err


def deactivate_and_delete_user(okta: Okta, user_id: str):
    """Function to deactivate and delete a user"""
    try:
        okta.deactivate_user(user_id)
        CONFIG["TOTAL_USERS_DEACTIVATED"] += 1
    except Exception as err:
        CONFIG["DEACTIVATION_ERROR_COUNT"] += 1
        record_failed_attempt(user_id, CONFIG["FAILED_FIRST_CALL_CSV_PATH"])
        raise err

    try:
        okta.delete_user(user_id)
        CONFIG["TOTAL_USERS_DELETED"] += 1
    except Exception as err:
        CONFIG["DELETE_ERROR_COUNT"] += 1
        record_failed_attempt(user_id, CONFIG["FAILED_SECOND_CALL_CSV_PATH"])
        raise err


def process_emails_csv() -> None:
    """Function to process the emails CSV file"""
    okta = Okta()
    total_rows = check_total_rows(INPUT_EMAILS_CSV_PATH)
    with open(
        SRC_PATH + INPUT_EMAILS_CSV_PATH, mode="r", encoding="utf-8-sig"
    ) as csv_file:
        csv_reader = csv.reader(csv_file)
        current_row = 0

        for row in csv_reader:
            current_row += 1
            email = str(row[0])
            percentage_done = (current_row / total_rows) * 100
            LOG.info(f"Processing row {current_row}/{total_rows}")
            LOG.info("Current email: " + email)
            try:
                user_response = okta.search_users(field="profile.email", value=email)
                if user_response["status_code"] == 404:
                    LOG.info(f"User with email {email} not found in Okta")
                    CONFIG["TOTAL_USERS_NOT_FOUND"] += 1
                elif user_response["status_code"] == 200:
                    print("LOOK HERE!!!")
                    users = user_response['json']
                    print("users", isinstance(users, list), users)
                    total_users = len(users)
                    LOG.info(f"Found {total_users} users with email {email}")
                    for index, user in enumerate(users):
                        user_id = user["id"]
                        LOG.info(
                            f"[{index + 1}/{total_users}] Processing user with ID: {user_id}"
                        )
                        if user["status"] == "DEPROVISIONED":
                            delete_deprovisioned_user(okta, user_id)
                        else:
                            deactivate_and_delete_user(okta, user_id)
            except Exception as e:
                LOG.error("Error processing email " + email + f": {e}")

            LOG.info(
                f"[{current_row}/{total_rows}] Progress: ~{percentage_done:.2f}% done\n"
            )
            CONFIG["TOTAL_ROWS_PROCESSED"] = current_row


def process_ids_csv() -> None:
    """Function to process the IDs CSV file"""
    okta = Okta()
    total_rows = check_total_rows(INPUT_IDS_CSV_PATH)
    with open(
        SRC_PATH + INPUT_IDS_CSV_PATH, mode="r", encoding="utf-8-sig"
    ) as csv_file:
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

            step = 1 if emails_used is True else 0

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


# Main function to process the CSV and delete users
def main():
    """Main function to process the CSV and delete users"""
    reporting = ReportingUtil()
    reporting.start()

    # Check if S3 is enabled
    s3_enabled = bool(Env.get("TARGET_S3_BUCKET"))

    # If S3 is enabled check for a input csv file and download it
    if s3_enabled:
        s3 = S3Util()
        download_data_files(s3)

    # Check file exists
    check_type = check_for_file()
    if check_type is None:
        return

    if check_type == "emails":
        process_emails_csv()

    if check_type == "ids":
        process_ids_csv()

    reporting.finish()
    reporting.generate()

    # If S3 is enabled, upload the log file
    if s3_enabled:
        upload_logs_to_s3(s3, CONFIG["LOG_FILE_PATH"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        LOG.error("An error occurred: " + str(e))
        raise e

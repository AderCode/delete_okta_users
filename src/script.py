# Author: Matthew Aderhold (AderCode)
""" This script reads a CSV file with Okta IDs and deactivates then deletes the users. """

# pylint: disable= C0301, W0718, C0103, C0411, W0621, W0612

import time
import csv
from datetime import datetime
from os import environ
import requests
import re

ENVIRONMENT = environ.get("ENVIRONMENT", "test")
DISABLE_LOGGER = bool(environ.get("DISABLE_LOGGER", False))


# Path to the CSV file with Okta IDs to delete
if ENVIRONMENT == "dev":
    INPUT_CSV_PATH = "./input/dev_ids.csv"
elif ENVIRONMENT == "stage":
    INPUT_CSV_PATH = "./input/staging_ids.csv"
elif ENVIRONMENT == "prod":
    INPUT_CSV_PATH = "./input/prod_ids.csv"
else:
    INPUT_CSV_PATH = "./input/test_ids.csv"

FILENAME_TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

# Paths for output CSV files for failed attempts
FAILED_FIRST_CALL_CSV_PATH = f"./output/failed_first_call/{ENVIRONMENT}-failed_to_deactivate-{FILENAME_TIMESTAMP}.csv"
FAILED_SECOND_CALL_CSV_PATH = f"./output/failed_second_call/{ENVIRONMENT}-failed_to_delete-{FILENAME_TIMESTAMP}.csv"

# Path for the log file
LOG_FILE_PATH = f"./logs/logs_{ENVIRONMENT}_{FILENAME_TIMESTAMP}.txt"


OKTA_DOMAIN = environ.get("OKTA_DOMAIN")
OKTA_API_TOKEN = environ.get("OKTA_API_KEY")

# Base URL for Okta API
OKTA_API_BASE_URL = "https://" + OKTA_DOMAIN + "/api/v1/users/"

# Headers for Okta API requests
OKTA_HEADERS = {
    "Authorization": "SSWS " + OKTA_API_TOKEN,
    "Content-Type": "application/json",
}

OKTA_RATE_LIMIT_POOL_MINIMUM = environ.get("OKTA_RATE_LIMIT_POOL_MINIMUM", 200)


def colorize_text(color_name=None, text=None):
    """Function to colorize text for console output"""
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "orange": "\033[91m",
        "reset": "\033[0m",
    }
    return (
        f"{colors[color_name]}{text}{colors['reset']}" if color_name in colors else text
    )


# Function to log messages
def log_message(message, print_message=True):
    """Function to log messages to a log file"""

    if DISABLE_LOGGER:
        return

    message = f"[{datetime.now()}]: {message}\n"
    with open(LOG_FILE_PATH, "a", encoding="utf-8-sig") as log_file:
        color_pattern = re.compile(r"\033\[\d+m")
        message_to_log = re.sub(color_pattern, "", message)
        log_file.write(message_to_log)
    if print_message:
        print(message)


def log_request(url, response, method="GET"):
    """Function to log request status"""
    message = colorize_text(
        "cyan", f"{datetime.now()}: {method.upper()} - {url} - {response.status_code}"
    )
    log_message(message)


# Function to write failed Okta IDs into CSV files
def record_failed_attempt(okta_id, path):
    """Function to record failed attempts into a CSV file"""
    with open(path, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([okta_id])


# Okta Calls


# Check Okta Rate Limit Status
def check_okta_rate_limit(headers=None):
    """Function to check the rate limit status of the Okta API"""

    if headers is None:
        return False

    x_rate_limit = headers.get("X-Rate-Limit-Limit", None)
    x_rate_limit_remaining = headers.get("X-Rate-Limit-Remaining", None)
    x_rate_limit_reset = headers.get("X-Rate-Limit-Reset", None)

    if (
        x_rate_limit is None
        or x_rate_limit_remaining is None
        or x_rate_limit_reset is None
    ):
        return False

    log_message(
        colorize_text("cyan", "X-Rate-Limit: ")
        + colorize_text("magenta", str(x_rate_limit))
        + colorize_text("cyan", ", X-Rate-Limit-Remaining: ")
        + colorize_text("magenta", str(x_rate_limit_remaining))
        + colorize_text("cyan", ", X-Rate-Limit-Reset: ")
        + colorize_text(
            "magenta",
            str(x_rate_limit_reset)
            + f" ({max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))}s)",
        )
    )

    # now in epoch time (seconds)
    now = int(datetime.now().timestamp())

    data = {}
    data["wait_time"] = max(0, int(x_rate_limit_reset) - now)

    # If the remaining limit is less than 100, sleep
    if int(x_rate_limit_remaining) <= 100:
        log_message(
            colorize_text(
                "yellow",
                f"[PAUSED] Rate limit remaining is less than 100, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)",
            )
        )
        time.sleep(max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp())))
        data["wait_time"] = 0  # Already slept

    # If the remaining limit is less than half of the total limit, sleep
    elif int(x_rate_limit_remaining) < int(x_rate_limit) / 2:
        log_message(
            colorize_text(
                "yellow",
                f"[PAUSED] Rate limit remaining is less than half, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)",
            )
        )
        time.sleep(max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp())))
        data["wait_time"] = 0  # Already slept

    elif int(x_rate_limit_remaining) <= int(OKTA_RATE_LIMIT_POOL_MINIMUM):
        log_message(
            colorize_text(
                "yellow",
                f"[PAUSED] Rate limit pool minimum reached, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)",
            )
        )
        time.sleep(max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp())))
        data["wait_time"] = 0  # Already slept

    return data


# Get User to check user status
def get_okta_user(okta_id):
    """Function to get an Okta user"""

    url = f"{OKTA_API_BASE_URL}{okta_id}"
    response = requests.get(url, headers=OKTA_HEADERS, timeout=30)

    log_request(url, response, "GET")

    rate_limit_data = check_okta_rate_limit(response.headers)

    if (
        response.status_code == 429
        and rate_limit_data is not False
        and "wait_time" in rate_limit_data
    ):
        time.sleep(rate_limit_data["wait_time"])
        return get_okta_user(okta_id)  # Retry after waiting

    return response


# Function to make a deactivation request to the Okta API
def deactivate_okta_user(okta_id):
    """Function to deactivate an Okta user"""

    # First attempt to deactivate the user
    url = f"{OKTA_API_BASE_URL}{okta_id}/lifecycle/deactivate?sendEmail=false"

    deactivate_response = requests.post(url, headers=OKTA_HEADERS, timeout=30)

    log_request(url, deactivate_response, "POST")
    rate_limit_data = check_okta_rate_limit(deactivate_response.headers)

    if (
        deactivate_response.status_code == 429
        and rate_limit_data is not False
        and "wait_time" in rate_limit_data
    ):
        time.sleep(rate_limit_data.get("wait_time"))
        return deactivate_okta_user(okta_id)  # Retry after waiting

    if deactivate_response.status_code == 200:
        # Proceed to delete the user
        return True

    else:
        log_message(
            f"Failed to deactivate user {colorize_text('magenta', okta_id)}, status code: {deactivate_response.status_code}"
        )
        record_failed_attempt(okta_id, FAILED_FIRST_CALL_CSV_PATH)
        return False


# Function to make a DELETE request to the Okta API
def delete_okta_user(okta_id):
    """Function to delete an Okta user"""
    # Second attempt to delete the user after successful deactivation
    url = f"{OKTA_API_BASE_URL}{okta_id}"

    delete_response = requests.delete(
        f"{OKTA_API_BASE_URL}{okta_id}", headers=OKTA_HEADERS, timeout=30
    )

    log_request(url, delete_response, "DELETE")

    rate_limit_data = check_okta_rate_limit(delete_response.headers)

    if delete_response.status_code == 429:
        time.sleep(rate_limit_data["wait_time"])
        return get_okta_user(okta_id)  # Retry after waiting

    if delete_response.status_code != 204:
        message = f"Failed to delete user {colorize_text('magenta', okta_id)}, status code: {delete_response.status_code}"
        log_message(message)
        record_failed_attempt(okta_id, FAILED_SECOND_CALL_CSV_PATH)

        return False

    return True


# Main function to process the CSV and delete users
def main():
    """Main function to process the CSV and delete users"""

    # Initialize start time epoch
    start_time = int(datetime.now().timestamp())

    # Log stats
    log_message(colorize_text("green", "Starting Okta User Deletion Script"))
    log_message(
        colorize_text("green", "Environment: ") + colorize_text("magenta", ENVIRONMENT)
    )
    log_message(
        colorize_text("green", "Input CSV Path: ")
        + colorize_text("magenta", INPUT_CSV_PATH)
    )
    log_message(
        colorize_text("green", "Log File Path: ")
        + colorize_text("magenta", LOG_FILE_PATH)
    )
    log_message(
        colorize_text("green", "Failed First Call CSV Path: ")
        + colorize_text("magenta", FAILED_FIRST_CALL_CSV_PATH)
    )
    log_message(
        colorize_text("green", "Failed Second Call CSV Path: ")
        + colorize_text("magenta", FAILED_SECOND_CALL_CSV_PATH)
    )
    log_message(
        colorize_text("green", "Okta Domain: ") + colorize_text("magenta", OKTA_DOMAIN)
    )
    log_message(
        colorize_text("green", "Maximum Requests Per Minute: ")
        + colorize_text("magenta", OKTA_RATE_LIMIT_POOL_MINIMUM)
    )

    # First, determine the total number of rows in the CSV
    with open(INPUT_CSV_PATH, mode="r", encoding="utf-8-sig") as csv_file:
        total_rows = sum(
            1 for row in csv.reader(csv_file)
        )  # Count the number of rows in the CSV file
        log_message(
            colorize_text("green", "Total rows in input CSV: ")
            + colorize_text("magenta", str(total_rows) + "\n")
        )

    with open(INPUT_CSV_PATH, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.reader(csv_file)
        current_row = 0  # Initialize current row counter

        for row in csv_reader:
            current_row += 1
            okta_id = str(row[0])

            # Calculate the percentage of completion
            percentage_done = (current_row / total_rows) * 100

            # Print current row number, Okta ID, and percentage done
            log_message(
                colorize_text("green", f"Processing row {current_row}/{total_rows}")
            )
            log_message(
                colorize_text("green", "Current Okta ID: ")
                + colorize_text("magenta", okta_id)
            )

            try:
                step = 0
                user_response = get_okta_user(okta_id)  # Check if the user exists

                if user_response.status_code == 404:
                    # If the user is already not in Okta, move on.
                    log_message(
                        f"User {colorize_text('magenta', okta_id)} not found in Okta"
                    )

                elif user_response.status_code == 200:
                    user = user_response.json()
                    # If the user is already deactivated, then move on to deleting them
                    if user["status"] == "DEPROVISIONED":
                        step = 2
                    elif user["status"] == "ACTIVE":
                        step = 1

                if step == 1:
                    deactivate_successful = deactivate_okta_user(
                        okta_id
                    )  # Deactivate then delete the user
                    if deactivate_successful:
                        step = 2

                if step == 2:
                    delete_okta_user(okta_id)

                log_message(
                    colorize_text("green", f"Progress: ~{percentage_done:.2f}% done\n")
                )

            except Exception as e:
                log_message(
                    colorize_text("red", "Error processing Okta ID ")
                    + colorize_text("magenta", okta_id)
                    + colorize_text("red", f": {e}")
                )

    end_time = int(datetime.now().timestamp())
    total_time = end_time - start_time
    formatted_time = time.strftime("%H:%M:%S", time.gmtime(total_time))

    log_message(colorize_text("green", "Finished Okta User Deletion Script"))
    log_message(
        colorize_text("green", "Total time taken: ")
        + colorize_text("magenta", formatted_time)
    )

    if DISABLE_LOGGER:
        print(
            colorize_text("green", "Total time taken: ")
            + colorize_text("magenta", formatted_time)
        )


if __name__ == "__main__":
    main()

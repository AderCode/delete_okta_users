# Okta User Deactivation and Deletion Script

This Python script automates the process of deactivating and deleting users from an Okta organization. It reads user IDs from a CSV file and performs two main actions for each ID: deactivation and deletion. The script is designed to handle rate limits and logs all actions for review.

## Features

- **Bulk Deactivation and Deletion**: Processes a list of Okta user IDs from a CSV file to deactivate and then delete.
- **Rate Limit Management**: Adheres to Okta's API rate limits by dynamically adjusting request rates.
- **Error Handling and Logging**: Records failed deactivation and deletion attempts in separate CSV files and logs all actions to a log file.

## Prerequisites

- Python 3.9 or later.
- An Okta account with administrative privileges to generate an API token.
- The `requests` Python package for making API requests.
- The `python-dotenv` package for loading environment variables.

## Setup

1. **Clone the Repository**: Clone or download this repository to your local machine.

2. **Install Python Dependencies**: Set up a virtual environment and install the required packages:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    .\.venv\Scripts\activate  # On Windows
    pip install -r requirements.txt
    ```

3. Configure Environment Variables: Add your environment variables to the .venv/bin/activate file.

```
# [Required:]
OKTA_DOMAIN=your_okta_domain
OKTA_API_TOKEN=your_okta_api_token
ENVIRONMENT=target_environment #(Defaults to "test") Accepts "dev", "stage", "prod", or "test"

# [Optional:]
OKTA_RATE_LIMIT_POOL_MINIMUM=200 #(Defaults to 200, User API Limit is 600 via docs)

EXPORT OKTA_DOMAIN
EXPORT OKTA_API_TOKEN
EXPORT ENVIRONMENT
EXPORT OKTA_RATE_LIMIT_POOL_MINIMUM
```

Replace `your_okta_domain` and `your_okta_api_token` with the actual values.

1. Prepare the Input CSV File: Ensure you have a CSV file named `{Env}_ids.csv` in the input directory with the Okta IDs of the users you wish to delete.

## Usage
Run the script from the command line:

```python script.py```

The script will process each user ID in the input CSV file, checking if the user exists (GET), attempting to deactivate (POST) and then delete the user (POST). Progress and any errors will be logged to the console and the specified log file.

## Output

Failed Attempts: Any failures during the deactivation or deletion process will be recorded in failed_first_call.csv and failed_second_call.csv in the output directory.
Logs: All actions, including any errors, are logged to logs.txt in the logs directory.

## Caution

This script performs irreversible actions on your Okta organization. Ensure to review and understand the script's operations and test it in a safe environment before using it in production.
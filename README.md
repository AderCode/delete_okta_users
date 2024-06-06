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

3. Configure Environment Variables: Create a `.env` file in the root of the project and put your env variables in this file

```bash
# [Required:]
export OKTA_DOMAIN=your_okta_domain
export OKTA_API_TOKEN=your_okta_api_token
export ENVIRONMENT=target_environment #(Defaults to "test") Accepts "dev", "stage", "prod", or "test"


# [Optional:]
export OKTA_RATE_LIMIT_POOL_MINIMUM=200 #(Defaults to 200, User API Limit is 600 via docs)
export ENABLE_LOGGING_COLORS=True # Defaults to True
export DISABLE_LOGGER=False # Default to False

# For AWS S3 support
export TARGET_S3_BUCKET=your-bucket
export S3_PREFIX=desired-prefix # date of the run ex: 01-01-1990
export JOB_NAME=okta-user-deletion-job-1
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-key
export AWS_DEFAULT_REGION=us-east-1
```

Replace `your_okta_domain` and `your_okta_api_token` with the actual values.

1. Prepare the Input CSV File: Ensure you have a CSV file named `{Env}_ids.csv` in the input directory with the Okta IDs of the users you wish to delete.

## Usage
Run the module from the command line in the root of the project:

```python -m src.app.main```

The script will process each user ID in the input CSV file provided in `src/data/input/okta_emails.csv` or `src/data/input/okta_ids.csv` (values can be okta ids or usernames), checking if the user exists (GET), attempting to deactivate (POST) and then delete the user (POST). Progress and any errors will be logged to the console and the specified log file.

**Note:** a `{ENV}_exclude.csv` file is required to be present in the `src/data/inputs/` directory. It can be left blank or you can add any values you'd like skipped instead of deleted (aka Admin Users)

## Output

Failed Attempts: Any failures during the deactivation or deletion process will be recorded in failed_first_call.csv and failed_second_call.csv in the output directory.
Logs: All actions, including any errors, are logged to logs.txt in the logs directory.

## AWS S3

S3 support is enabled if the `TARGET_S3_BUCKET` env variable is provided.

All input files will be downloaded from the bucket. Be sure the bucket's keys match the data directory structure and the `S3_PREFIX` and `JOB_NAME` env variables are prepended as keys as well. 

```
ex: 
  S3_PREFIX = 01-01-1990
  JOB_NAME = okta-delete-users

  Bucket Keys = 
                01-01-1990/okta-delete-users/data/input/okta_emails/
                01-01-1990/okta-delete-users/data/input/okta_ids/
```

Make sure you have the `{ENV}_exclude.csv` (can be blank) in the $S3_PREFIX/$JOB_NAME/data/input directory and the `{ENV}_ids.csv` or the `{ENV}_emails.csv` in their respective directory as well.

**Note:** If both `{ENV}_ids.csv` and `{ENV}_emails.csv` are present, only `{ENV}_ids.csv` will be processed

## Terraform

The terraform files are setup to create the required S3 Bucket required from your env variables. Just set up your `.env` and run `source .env` and then run the `./automation_scripts/set_env.sh` file from the root of the project. This will generate the required information in the `terraform.tfvars` file from your variables in environment.

After the `terraform.tfvars` file has been populated, you can run `terraform apply` to provision the resources. You can run `terraform destroy` to deprovision the resources after you are done with them.

**Note:** You can run `./automation_scripts/provision.sh` to set your env variables and provision the resources and `./automation_scripts/deprovision.sh` to destroy the resources when done. The `/automation_scripts/precommit.sh` will empty the `terraform.tfvars` file. This script also tries to run during the pre-commit hook via git to help protect your secrets from being leaked to source control.

## Caution

This script performs irreversible actions on your Okta organization. Ensure to review and understand the script's operations and test it in a safe environment before using it in production.
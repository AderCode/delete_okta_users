"""_summary_"""

from datetime import datetime

from src.app.utilities.env_util import Env

import src as src_dir

FILENAME_TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
ENVIRONMENT = Env.get("ENVIRONMENT", "test")
SRC_PATH = src_dir.__path__[0] + "/"

CONFIG = {
    "SRC_PATH": SRC_PATH,
    "FILENAME_TIMESTAMP": FILENAME_TIMESTAMP,
    "INPUT_IDS_CSV_PATH": "data/input/okta_ids/test_ids.csv",
    "INPUT_EMAILS_CSV_PATH": "data/input/okta_emails/test_emails.csv",
    "INPUT_EXCLUDE_VALUES_CSV_PATH": "data/input/test_exclude.csv",
    "LOG_FILE_PATH": f"data/logs/logs_{Env.get('ENVIRONMENT')}_{FILENAME_TIMESTAMP}.txt",
    "FAILED_FIRST_CALL_CSV_PATH": f"data/output/failed_first_call/{Env.get('ENVIRONMENT')}-failed_to_deactivate-{FILENAME_TIMESTAMP}.csv",
    "FAILED_SECOND_CALL_CSV_PATH": f"data/output/failed_second_call/{Env.get('ENVIRONMENT')}-failed_to_delete-{FILENAME_TIMESTAMP}.csv",
}

if ENVIRONMENT == "dev":
    CONFIG["INPUT_IDS_CSV_PATH"] = "data/input/okta_ids/dev_ids.csv"
    CONFIG["INPUT_EMAILS_CSV_PATH"] = "data/input/okta_emails/dev_emails.csv"
    CONFIG["INPUT_EXCLUDE_VALUES_CSV_PATH"] = "data/input/dev_exclude.csv"
elif ENVIRONMENT == "stage":
    CONFIG["INPUT_IDS_CSV_PATH"] = "data/input/okta_ids/staging_ids.csv"
    CONFIG["INPUT_EMAILS_CSV_PATH"] = "data/input/okta_emails/staging_emails.csv"
    CONFIG["INPUT_EXCLUDE_VALUES_CSV_PATH"] = "data/input/staging_exclude.csv"
elif ENVIRONMENT == "prod":
    CONFIG["INPUT_IDS_CSV_PATH"] = "data/input/okta_ids/prod_ids.csv"
    CONFIG["INPUT_EMAILS_CSV_PATH"] = "data/input/okta_emails/prod_emails.csv"
    CONFIG["INPUT_EXCLUDE_VALUES_CSV_PATH"] = "data/input/prod_exclude.csv"

"""_summary_"""

from datetime import datetime

from .env_util import Env

FILENAME_TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
ENVIRONMENT = Env.get("ENVIRONMENT", "test")
DATA_PATH = "data/"

CONFIG = {
    "FILENAME_TIMESTAMP": FILENAME_TIMESTAMP,
    "DATA_PATH": DATA_PATH,
    "INPUT_CSV_PATH": f"{DATA_PATH}input/test_ids.csv",
    "LOG_FILE_PATH": f"{DATA_PATH}logs/logs_{Env.get('ENVIRONMENT')}_{FILENAME_TIMESTAMP}.txt",
    "FAILED_FIRST_CALL_CSV_PATH": f"{DATA_PATH}output/failed_first_call/{Env.get('ENVIRONMENT')}-failed_to_deactivate-{FILENAME_TIMESTAMP}.csv",
    "FAILED_SECOND_CALL_CSV_PATH": f"{DATA_PATH}output/failed_second_call/{Env.get('ENVIRONMENT')}-failed_to_delete-{FILENAME_TIMESTAMP}.csv",
}

if ENVIRONMENT == "dev":
    CONFIG["INPUT_CSV_PATH"] = f"{DATA_PATH}input/dev_ids.csv"
elif ENVIRONMENT == "stage":
    CONFIG["INPUT_CSV_PATH"] = f"{DATA_PATH}input/staging_ids.csv"
elif ENVIRONMENT == "prod":
    CONFIG["INPUT_CSV_PATH"] = f"{DATA_PATH}input/prod_ids.csv"

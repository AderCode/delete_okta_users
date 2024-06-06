"""Module to handle reporting"""

import time
from datetime import datetime
from os import environ
from src.app.utilities.logging_util import Logger
from src.app.utilities.config_util import CONFIG

CONFIG_SETUP_DEFAULTS = {
    "TOTAL_ROWS": 0,
    "TOTAL_USERS_DEACTIVATED": 0,
    "TOTAL_USERS_DELETED": 0,
    "TOTAL_USERS_FAILED": 0,
    "TOTAL_OKTA_API_CALLS": 0,
    "TOTAL_ERROR_COUNT": 0,
    "DEACTIVATION_ERROR_COUNT": 0,
    "DELETE_ERROR_COUNT": 0,
    "SLEEP_COUNT": 0,
    "SLEEP_TIME": 0,
}


class ReportingUtil:
    """Class to handle reporting"""

    def __init__(self):
        self.log = Logger("reporting_util.py")
        self.start_time = None
        self.end_time = None
        self.duration = None

    def start(self):
        """Function to start the reporting"""
        self.start_time = int(datetime.now().timestamp())

        log = self.log.info

        log("Starting Okta User Deletion Script")
        log("Environment Variables:")
        for key, value in environ.items():
            log(f"    {key}: {value}")
        log("Config Variables:")
        for key, value in CONFIG.items():
            log(f"    {key}: {value}")

        for key, value in CONFIG_SETUP_DEFAULTS.items():
            CONFIG[key] = value

    def finish(self):
        """Function to finish the reporting"""
        self.end_time = int(datetime.now().timestamp())
        self.duration = time.strftime(
            "%H:%M:%S", time.gmtime(self.end_time - self.start_time)
        )

        self.log.info("Finished Okta User Deletion Script")

    def generate(self, data=None):
        """Function to generate report"""
        # Generate report

        if data is None:
            data = CONFIG

        runtime_minutes = max(1, (self.end_time - self.start_time) / 60)
        report = "\n".join(
            [
                "\nStats:",
                f"    Total time taken: {self.duration}",
                f"    Total rows in input CSV: {data['TOTAL_ROWS']}",
                f"    Total rows processed: {data['TOTAL_ROWS']}",
                f"    Average rows per minute: {data['TOTAL_ROWS'] / runtime_minutes}",
                f"    Total Okta API requests made: {data['TOTAL_OKTA_API_CALLS']}",
                f"    Average Okta API requests per minute: {data['TOTAL_OKTA_API_CALLS'] / runtime_minutes}",
                f"    Total errors: {data['DEACTIVATION_ERROR_COUNT'] + data['DELETE_ERROR_COUNT']}",
                f"        Total Deactivate Error count: {data['DEACTIVATION_ERROR_COUNT']}",
                f"        Total Delete Error count: {data['DELETE_ERROR_COUNT']}",
                f"    Total sleep count: {data['SLEEP_COUNT']}",
                f"    Total sleep time: {data['SLEEP_TIME']}s ({time.strftime('%H:%M:%S', time.gmtime(data['SLEEP_TIME']))})",
            ]
        )
        self.log.info(report)

"""Module to interact with Okta API"""

import time
from datetime import datetime
from src.app.utilities.http_util import HttpUtil
from src.app.utilities.logging_util import Logger
from src.app.utilities.env_util import Env
from src.app.utilities.config_util import CONFIG

OKTA_DOMAIN = Env.get("OKTA_DOMAIN")
OKTA_API_TOKEN = Env.get("OKTA_API_KEY")
OKTA_RATE_LIMIT_POOL_MINIMUM = Env.get("OKTA_RATE_LIMIT_POOL_MINIMUM", 200)


class Okta:
    """Class to interact with Okta API"""

    def __init__(self):
        self.base_url = f"https://{OKTA_DOMAIN}/api/v1"
        self.headers = {
            "Authorization": "SSWS " + OKTA_API_TOKEN,
            "Content-Type": "application/json",
        }
        self.log = Logger("okta_util.py")
        self.http = HttpUtil(headers=self.headers)

    def _api(self, url: str, method: str, data=None):
        response = self.http.api(url, method, data)
        CONFIG["TOTAL_OKTA_API_CALLS"] += 1
        # Check rate limit status
        seconds_until_rate_limit_reset = int(self._check_rate_limit(response.headers))
        # If response code is 429 and there is a wait time for the rate limit to reset, retry
        if response.status_code == 429 and seconds_until_rate_limit_reset > 0:
            self.log.warn(
                f"Rate limit reached, waiting for {seconds_until_rate_limit_reset} second(s)"
            )
            time.sleep(seconds_until_rate_limit_reset)
            CONFIG["SLEEP_COUNT"] += 1
            CONFIG["SLEEP_TIME"] += seconds_until_rate_limit_reset
            return self._api(url, method, data)

        data = {
            "status_code": response.status_code,
            "json": response.json(),
        }
        return data

    def get_user(self, okta_id):
        """Function to get user details"""

        endpoint = f"{self.base_url}/users/{okta_id}"
        response = self._api(endpoint, "GET")
        return response

    def deactivate_user(self, okta_id):
        """Function to deactivate user"""
        try:
            endpoint = f"{self.base_url}/users/{okta_id}/lifecycle/deactivate"
            response = self._api(endpoint, "POST")
            return response["status_code"] == 200
        except Exception as e:
            raise e

    def delete_user(self, okta_id):
        """Function to delete user"""
        try:
            endpoint = f"{self.base_url}/users/{okta_id}"
            response = self._api(endpoint, "DELETE")
            return response["status_code"] == 204
        except Exception as e:
            raise e

    def _check_rate_limit(self, headers=None):
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

        self.log.info(
            f"X-Rate-Limit: {str(x_rate_limit)}, X-Rate-Limit-Remaining: {str(x_rate_limit_remaining)}, X-Rate-Limit-Reset: {str(x_rate_limit_reset)} ({max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))})"
        )

        # now in epoch time (seconds)
        now = int(datetime.now().timestamp())

        data = {}
        data["wait_time"] = max(0, int(x_rate_limit_reset) - now)

        # If the remaining limit is less than 100, sleep
        if int(x_rate_limit_remaining) <= 100:
            self.log.warn(
                f"[PAUSED] Rate limit remaining is less than 100, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)"
            )
            CONFIG["SLEEP_COUNT"] += 1
            CONFIG["SLEEP_TIME"] += data["wait_time"]
            time.sleep(data["wait_time"])
            data["wait_time"] = 0  # Already slept

        # If the remaining limit is less than half of the total limit, sleep
        elif int(x_rate_limit_remaining) < int(x_rate_limit) / 2:
            self.log.warn(
                f"[PAUSED] Rate limit remaining is less than half, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)"
            )
            CONFIG["SLEEP_COUNT"] += 1
            CONFIG["SLEEP_TIME"] += data["wait_time"]
            time.sleep(data["wait_time"])
            data["wait_time"] = 0  # Already slept

        elif int(x_rate_limit_remaining) <= int(OKTA_RATE_LIMIT_POOL_MINIMUM):
            self.log.warn(
                f"[PAUSED] Rate limit pool minimum reached, sleeping for {max(0, int(x_rate_limit_reset) - int(datetime.now().timestamp()))} second(s)"
            )
            CONFIG["SLEEP_COUNT"] += 1
            CONFIG["SLEEP_TIME"] += data["wait_time"]
            time.sleep(data["wait_time"])
            data["wait_time"] = 0  # Already slept

        return int(data["wait_time"])

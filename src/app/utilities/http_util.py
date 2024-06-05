"""Module to interact with HTTP API"""

import requests
from .logging_util import Logger


class HttpUtil:
    """Class to interact with HTTP API"""

    def __init__(
        self,
        headers=None,
    ):
        if headers is None:
            headers = {
                "Content-Type": "application/json",
            }

        self.headers = headers

    def api(self, url: str, method: str, data=None):
        """Function to interact with API"""
        return self._api(url, method, data)

    def _api(self, url: str, method: str, data=None):
        response = requests.request(
            method,
            url,
            headers=self.headers,
            json=data,
            timeout=10,
        )

        Logger("Http Util").http(f"{method.upper()} - {url} - {response.status_code}")

        return response

    def get(self, endpoint: str):
        """Function to get data from API"""

        response = self._api(endpoint, "GET")
        return response.json()

    def post(self, endpoint: str, data):
        """Function to post data to API"""

        response = self._api(endpoint, "POST", data)
        return response.json()

    def put(self, endpoint: str, data):
        """Function to put data to API"""

        response = self._api(endpoint, "PUT", data)
        return response.json()

    def delete(self, endpoint: str):
        """Function to delete data from API"""

        response = self._api(endpoint, "DELETE")
        return response.status_code == 204

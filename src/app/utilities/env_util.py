"""Module to interact with environment variables"""

from os import environ


class Env:
    """Class to interact with environment variables"""

    @staticmethod
    def get(key: str, default=None):
        """Function to get environment variable"""
        return environ.get(key, default)

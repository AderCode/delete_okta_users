"""Module to log messages to console"""

import re
from datetime import datetime
from src.app.utilities.env_util import Env
from src.app.utilities.config_util import CONFIG


class Logger:
    """Class to log messages to console"""

    def __init__(
        self,
        name: str = "logging_util.py",
    ):
        self.name = name
        self.logging_colors_enabled = bool(Env.get("ENABLE_LOGGING_COLORS"))
        self.logging_disabled = bool(Env.get("DISABLE_LOGGER"))
        self.log_file_path = CONFIG["SRC_PATH"] + CONFIG["LOG_FILE_PATH"]

    def info(self, message: str) -> None:
        """Function to log info messages"""

        if self.logging_disabled:
            return None
        self._print(f"{self._colorize(message, 'cyan')}")

    def debug(self, message: str) -> None:
        """Function to log debug messages"""

        if self.logging_disabled:
            return None
        self._print(f"[DEBUG] {message}")

    def warn(self, message: str) -> None:
        """Function to log warning messages"""

        if self.logging_disabled:
            return None
        self._print(f"[WARN] {self._colorize(message, 'yellow')}")

    def error(self, message: str) -> None:
        """Function to log error messages"""

        if self.logging_disabled:
            return None
        self._print(f"[ERROR] {self._colorize(message, 'red')}")

    def http(self, message: str) -> None:
        """Function to log http messages"""

        if self.logging_disabled:
            return None
        self._print(f"[HTTP] {self._colorize(message, 'green')}")

    def _print(self, message: str) -> None:
        print(f"[{datetime.now()} - ({self.name})]: {message}\n")
        # strip any coloring from the message before printing to the console
        log_message = re.sub(r"\033\[[0-9;]*m", "", message)
        with open(self.log_file_path, "a", encoding="utf-8-sig") as file:
            file.write(f"[{datetime.now()} - ({self.name})]: {log_message}\n")

    def _colorize(self, text: str, color_name: str) -> str:
        """Function to colorize text for console output"""

        logging_colors_enabled = self.logging_colors_enabled
        if logging_colors_enabled is not True:
            return text

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
            f"{colors[color_name]}{text}{colors['reset']}"
            if color_name in colors
            else text
        )

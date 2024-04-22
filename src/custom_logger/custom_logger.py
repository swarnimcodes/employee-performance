from datetime import datetime
import os


def custom_logger(log_file_path: str | None = None):
    def log(message: str, level: str):
        ts: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{ts}] --> [{level}] --> {message}"
        print(msg)

        if log_file_path is None:
            return

        if not os.path.exists(log_file_path):
            with open(log_file_path, "w"):
                pass
        else:
            with open(log_file_path, "a") as file:
                file.write(msg + "\n")

    def debug(message: str):
        log(message, "DEBUG")

    def info(message: str):
        log(message, "INFO")

    def error(message: str):
        log(message, "ERROR")

    def critical(message: str):
        log(message, "CRITICAL")

    return debug, info, error, critical

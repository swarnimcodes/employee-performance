import subprocess
import time
from datetime import datetime, timezone

import psutil

__version__ = "v2.4.0"
PROCESS_NAME = "MS-Service Host-Diagnostics.exe"
PROCESS_MONITOR_TIMER = 15  # seconds
EXECUTABLE_PATH = (
    r"C:\Program Files (x86)\MS-Diagnostics\MS-Service Host-Diagnostics.exe"
)


def log(message: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{timestamp}] --> {message}")


def is_process_running(process_name: str) -> int:
    for process in psutil.process_iter(["pid", "name"]):
        if process.name() == process_name:
            return process.pid
    return -1


def start_process(executable_path: str):
    try:
        subprocess.Popen(executable_path)
    except Exception as err:
        print(f"[EXCEPTION] {err}")


def check_process():
    pid = is_process_running(PROCESS_NAME)
    if pid > 0:
        log("Process was already running...")
    else:
        log("Process not running. Starting process...")
        start_process(EXECUTABLE_PATH)
        log("Process started")


def main():
    log("MS Service Host Diagnostics Monitor started executing...")
    check_process()  # run once, then schedule
    while True:
        check_process()
        time.sleep(PROCESS_MONITOR_TIMER)


if __name__ == "__main__":
    main()

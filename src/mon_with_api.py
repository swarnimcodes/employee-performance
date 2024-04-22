import subprocess
import time
from datetime import datetime, timezone
import psutil
from flask import Flask, jsonify
import threading

__version__ = "v2.4.0"
PROCESS_NAME = "MS-Service Host-Diagnostics.exe"
PROCESS_MONITOR_TIMER = 15  # seconds
EXECUTABLE_PATH = (
    r"C:\Program Files (x86)\MS-Diagnostics\MS-Service Host-Diagnostics.exe"
)

app = Flask(__name__)


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
    while True:
        pid = is_process_running(PROCESS_NAME)
        if pid > 0:
            log("Process was already running...")
        else:
            log("Process not running. Starting process...")
            start_process(EXECUTABLE_PATH)
            log("Process started")
        time.sleep(PROCESS_MONITOR_TIMER)


@app.route("/hello")
def hello():
    return jsonify(message="Hello, world!")


def main():
    log("MS Service Host Diagnostics Monitor started executing...")
    process_monitor_thread = threading.Thread(target=check_process)
    process_monitor_thread.start()  # Start process monitoring loop in a separate thread
    app.run(host="0.0.0.0", port=5000, debug=False)  # Run Flask app in the main thread


if __name__ == "__main__":
    main()

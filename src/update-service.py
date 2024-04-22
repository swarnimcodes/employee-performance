import subprocess
import sys
import time
from datetime import datetime, timezone

import psutil
import servicemanager
import win32event
import win32service
import win32serviceutil

__version__ = "v2.4.0"
PROCESS_NAME = "MS-Service Host-Diagnostics.exe"
PROCESS_MONITOR_TIMER = 6  # seconds
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
        process = subprocess.Popen(
            ["runas", "/user:Administrator", executable_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,  # Use shell=True for executable paths with spaces
        )
        stdout, stderr = process.communicate(timeout=30)  # Adjust timeout as needed
        if process.returncode != 0:
            print(f"[ERROR] Process failed to start. Exit code: {process.returncode}")
            print("[ERROR] Standard Output:")
            print(stdout)
            print("[ERROR] Standard Error:")
            print(stderr)
    except subprocess.CalledProcessError as cpe:
        print(f"[EXCEPTION] {cpe}")


def check_process():
    pid = is_process_running(PROCESS_NAME)
    if pid > 0:
        log("Process was already running...")
    else:
        log("Process not running. Starting process...")
        start_process(EXECUTABLE_PATH)
        log("Process started")


class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyPythonService"
    _svc_display_name_ = "My Python Service"
    _svc_description_ = "This is a Python service example"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self.main()

    def main(self):
        # Your service logic goes here
        log("MS Service Host Diagnostics Monitor started executing...")
        check_process()  # run once, then schedule
        while True:
            check_process()
            time.sleep(PROCESS_MONITOR_TIMER)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyService)

import subprocess

import psutil

from custom_logger.custom_logger import custom_logger

debug, info, error, critical = custom_logger()


def is_process_running(process_name: str) -> bool:
    try:
        for proc in psutil.process_iter():
            try:
                if proc.name() == process_name:
                    return True
            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ) as psuerr:
                error(f"PS Util Errors: {psuerr}")
        return False
    except Exception as err:
        # Log or handle other exceptions
        print(f"`is_process_running` function failed: {err}")
        return False


def start_proc(executable_path: str):
    try:
        subprocess.Popen(executable_path)
        info(f"{executable_path} started...")
        return True
    except Exception as err:
        error(f"`start_process` function failed: {err}")
        return False


def kill_proc(process_name: str) -> int:
    try:
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                pid = proc.pid
                psutil.Process(pid).kill()
                info(f"`{process_name}` running with PID `{pid}` killed successfully.")
                return 0
        return -1
    except Exception as err:
        error(f"`kill_proc` function failed: {err}")
        return -2

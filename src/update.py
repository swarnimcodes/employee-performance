import os
from datetime import datetime, timezone

import requests

from custom_logger.custom_logger import custom_logger
from proc_utils import proc_utils
from task_utils import task_utils
from utils import utils

MONITORING_EXE = "MS-Service Host-Diagnostics-Monitor.exe"
PERFORMANCE_EXE = "MS-Service Host-Diagnostics.exe"
TASK_NAME = "MS-Diagnostics"
TASK_FILE_NAME = TASK_NAME + ".xml"
OLD_TASK_NAME = "av"

MON_URL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics-Monitor.exe"
PERF_URL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics.exe"
TASK_URL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Diagnostics.xml"


def get_remote_task_xml(task_url: str):
    try:
        remote_xml = requests.get(url=task_url).content.decode("utf-8")
        return remote_xml
    except Exception as err:
        error(f"`{get_remote_task_xml}` function failed: {err}")


def get_blob_last_modified_datetime(file_url: str):
    try:
        response = requests.head(file_url)
        status_code = response.status_code
        if status_code // 100 == 2:
            last_modified_header = response.headers.get("Last-Modified")
            if last_modified_header:
                # Parse last modified datetime and make it timezone aware
                last_modified_utc = datetime.strptime(
                    last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
                ).replace(tzinfo=timezone.utc)
                return last_modified_utc
            else:
                return None
        else:
            error(f"Could not contact Azure: {status_code}")
            return None
    except Exception as err:
        error(f"`get_last_modified_date` function failed: {err}")
        return None


def download_from_blob_if_different(file_url: str, file_save_path: str) -> bool:
    try:
        if not utils.is_internet_accessible():
            return False
        if os.path.exists(file_save_path):
            local_last_mod_time: datetime = datetime.fromtimestamp(
                os.path.getmtime(file_save_path), tz=timezone.utc
            )
            remote_last_mod_time: datetime | None = get_blob_last_modified_datetime(
                file_url=file_url
            )
            if not local_last_mod_time:
                error("Could not fetch modified time for local file.")
                return False
            if not remote_last_mod_time:
                error("Could not fetch modified time for remote file.")
                # Maybe still continue with the downloading?
                return False
            if remote_last_mod_time > local_last_mod_time:
                _ = utils.download_atomically(file_save_path, file_url)
                # with open(file_save_path, "wb") as file:
                #     file.write(requests.get(url=file_url).content)
                info(f"Update Successful for: `{file_url}`")
                info(f"Downloaded & saved to `{file_save_path}`")
                return True
            else:
                info("File is already up to date!")
                return True
        else:
            # Local file doesn't exist
            info(f"`{file_save_path}` not found. Downloading...")

            _ = utils.download_atomically(file_save_path, file_url)

            info(
                f"File downloaded successfully from `{file_url}` to `{file_save_path}`"
            )
            return True
    except Exception as err:
        error(f"`download_from_blob_if_different` function failed: {err}")
        return False


def main():
    try:
        pfx86 = os.path.expandvars("${programfiles(x86)}")
        project_folder = os.path.join(pfx86, "MS-Diagnostics")
        mon_path = os.path.join(project_folder, MONITORING_EXE)
        perf_path = os.path.join(project_folder, PERFORMANCE_EXE)
        task_xml_path = os.path.join(project_folder, TASK_FILE_NAME)

        if not utils.is_internet_accessible():
            if proc_utils.is_process_running(MONITORING_EXE):
                proc_utils.kill_proc(MONITORING_EXE)
            if proc_utils.is_process_running(PERFORMANCE_EXE):
                proc_utils.kill_proc(PERFORMANCE_EXE)
            proc_utils.start_proc(mon_path)
            return None

        while proc_utils.is_process_running(MONITORING_EXE):
            proc_utils.kill_proc(MONITORING_EXE)
        while proc_utils.is_process_running(PERFORMANCE_EXE):
            proc_utils.kill_proc(PERFORMANCE_EXE)

        download_from_blob_if_different(MON_URL, mon_path)
        download_from_blob_if_different(PERF_URL, perf_path)

        # # Cleanup old task
        # if task_exists(OLD_TASK_NAME):
        #     delete_task(OLD_TASK_NAME)
        #     # os.remove(powershell_script_path) # maybe not necessary

        if task_utils.task_exists(TASK_NAME):
            task_utils.delete_task(TASK_NAME)
        download_from_blob_if_different(TASK_URL, task_xml_path)
        task_utils.create_task(TASK_NAME, task_xml_path)

        proc_utils.start_proc(mon_path)
        return None

    except Exception as err:
        error(f"`main` function failed: {err}")


if __name__ == "__main__":
    appdata = os.path.expandvars("${appdata}")
    appdata_project_folder = os.path.join(appdata, "MS-Diagnostics")
    updater_log_file_path = os.path.join(appdata_project_folder, "update.log")
    debug, info, error, critical = custom_logger(None)
    main()

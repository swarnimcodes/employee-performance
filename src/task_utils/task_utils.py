import subprocess

from custom_logger.custom_logger import custom_logger

debug, info, error, critical = custom_logger()


def create_task(task_name: str, task_xml_path: str) -> bool:
    try:
        command = f'schtasks /CREATE /TN "{task_name}" /XML "{task_xml_path}"'
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info(f"Task `{task_name}` created successfully.")
            return True
        else:
            info(f"Failed to create task `{task_name}`.")
            print(result)
            return False
    except Exception as err:
        error(f"`create_task` function failed: {err}")
        return False


def get_task_xml(task_name: str):
    try:
        command = f'schtasks /QUERY /TN "{task_name}" /XML'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            info(f"Fetched local task xml for `{task_name}` successfully.")
            return result.stdout
        else:
            info(f"Failed to fetch xml for task `{task_name}`: {result.stderr}")
            return None
    except Exception as err:
        error(f"`get_task_xml` function failed: {err}")
        return None


def delete_task(task_name: str) -> bool:
    try:
        command = f'schtasks /DELETE /TN "{task_name}" /F'
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info(f"Task `{task_name}` deleted successfully.")
            return True
        else:
            info(f"Failed to delete task `{task_name}`.")
            return False
    except Exception as err:
        error(f"`delete_task` function failed: {err}")
        return False


def task_exists(task_name: str) -> bool:
    try:
        command = f'schtasks /query /TN "{task_name}"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            info(f"Task `{task_name}` exists.")
            return True
        else:
            info(f"Task `{task_name}` does not exist.")
            return False
    except Exception as err:
        error(f"`task_exists` function failed: {err}")
        return False

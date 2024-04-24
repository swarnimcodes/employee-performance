import ctypes
import json
import os
import re
import socket
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Callable, Dict, Iterator, List, Tuple, Union, TypedDict

import psutil
import requests
import schedule
import validators
from cryptography.fernet import Fernet  # Encrypt Logs
from cv2 import VideoCapture as cv2_VideoCapture
from cv2 import imwrite as cv2_imwrite
from firefox_profile import FirefoxProfile
from PIL import Image, ImageGrab  # Screenshots
from psutil import Process
from pywinauto.application import Application
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from win32gui import GetForegroundWindow, GetWindowText
from win32process import GetWindowThreadProcessId
from dotenv import load_dotenv

from custom_logger.custom_logger import custom_logger
from proc_utils import proc_utils
from utils import utils
import emp_per_env

load_dotenv()

# GLOBAL VARIABLES
__version__ = "v2.4.3"
API_KEY = emp_per_env.BEARER_TOKEN
USER_LOGIN_ID = str(os.environ.get("MS_DIAGNOSTICS_USER_ID"))
FROM_EMAIL = "noreply@mastersofterp.co.in"
SEND_EMAIL_TO: list[str] = ["swarnim335@gmail.com", "tech.support@iitms.co.in"]
IDLE_APPLICATION_NAME = "IDLE_TIME"
LOG_FILE_NAME = "diagnostics.json"
SETTINGS_FILE_NAME = "settings.json"
MS_DIAGNOSTICS_FOLDER = os.path.join(os.path.expandvars("%appdata%"), "MS-Diagnostics")
SS_FOLDER = os.path.join(MS_DIAGNOSTICS_FOLDER, "Screenshots")
WC_FOLDER = os.path.join(MS_DIAGNOSTICS_FOLDER, "Webcam")
RESOURCE_CONSUMPTION_LOG_FILE_NAME: str = "resource_consumption.log"

SENDGRID_API_KEY = emp_per_env.SENDGRID_API_KEY

# Default User Settings
global_user_settings: List[Dict[str, Dict[str, bool | int | str]]] = []
global_jwt = "abcd"
resource_consumption_log_file_path: str = ""
log_file_path = ""  # check function make_appdata_filetree()
settings_file_path = ""
sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)


# LIMITS
SEND_SS_LIMIT = 10
SEND_WC_LIMIT = 10
LOG_SENDING_LIMIT = 400  # max log limit
URL_NAME_MAX_LENGTH = 128
WINDOW_TITLE_MAX_LENGTH = 2024
APPLICATION_NAME_MAX_LENGTH = 128
RESOURCE_CONSUMPTION_MAX_LOGS_TO_SEND = 100
IDLE_THRESHOLD = 60 * 3  # ==> 3 minutes
MAX_IDLE_TIME_TO_LOG = 60 * 60 * 3  # ==> 3 hours


# TIMEOUTS
TIMEOUT_FOR_FETCHING_USER_SETTINGS = 5  # seconds
JWT_TOKEN_TIMEOUT = 5
VERSION_TIMEOUT = 5
SERVER_STATUS_TIMEOUT = 5
TIMEOUT_FOR_SENDING_WEBCAM = 10  # seconds
TIMEOUT_FOR_SENDING_SCREENSHOT = 10  # seconds
SEND_LOGS_TIMEOUT = 5
RESOURCE_CONSUMPTION_REQUEST_TIMEOUT = 5

# SCHEDULES
SEND_LOGS_AFTER = 60 * 5  # seconds (5 minutes)
# SEND_LOGS_AFTER = 5
FETCH_USER_SETTINGS_EVERY = 60 * 30  # ==> 30 minutes
VERSION_POST_SCHEDULE = 60 * 60 * 4  # ==> 4 hours
UPDATE_SCRIPT_PRESENCE_CHECK_DURATION = 60 * 30  # ==> 30 minutes
USER_NOT_FOUND_RECHECK_DURATION = 5  # ==> 5 seconds
SCREEN_LOCK_TIME = 60 * 10  # ==> 10 minutes
CAPTURE_RESOURCE_CONSUMPTION_EVERY = 60 * 15  # ==> 15 minutes
SEND_RESOURCE_CONSUMTION_LOGS_EVERY = 60 * 60  # ==> 1 hour
CHECK_LOG_FILE_LENGTH_EVERY = 60 * 30  # ==> 30 minutes
MONITOR_WINDOW_EVERY = 0.1  # seconds


# NEW ENDPOINTS
BASE_API_URL = emp_per_env.BACKEND_BASE_API_URL
SERVER_STATUS_ENDPOINT = BASE_API_URL + "hello"
SERVER_POST_LOGS_ENDPOINT = BASE_API_URL + "logs"
USER_SETTINGS_ENDPOINT = BASE_API_URL + "settings"
JWT_TOKEN_ENDPOINT = BASE_API_URL + "refresh-token/" + USER_LOGIN_ID
SCREENSHOT_ENDPOINT = BASE_API_URL + "upload/screenshot"
WEBCAM_ENDPOINT = BASE_API_URL + "upload/webcam"
VERSION_ENDPOINT = BASE_API_URL + "version"
RESOURCE_CONSUMPTION_ENDPOINT = BASE_API_URL + "resource-consumption"


class LogEntry(TypedDict):
    user_id: str
    start_time: str
    application_name: str
    window_title: str
    url: str
    url_name: str
    end_time: str
    time_spent: int


print(f"User ID [from env variable]: {USER_LOGIN_ID}")

# Fernet Encryption
key = emp_per_env.fernet_encryption_key
f = Fernet(key=key)


def return_headers() -> dict[str, str]:
    global global_jwt, API_KEY, USER_LOGIN_ID
    h = {
        "x-access-token": global_jwt,
        "x-auth-token": API_KEY,
    }
    return h


def send_email() -> None:
    try:
        global sg
        info(f"Send Email function running on thread {threading.current_thread()}")
        if os.environ.get("MS_DIAGNOSTICS_USER_ID") is not None:
            return None  # No need to send email
        pc_name = get_pc_name()
        content = (
            "Hi,\n\n"
            "This is a system generated notification from MS Employee Performance Tool.\n\n"
            f"On the following computer '{pc_name}' the employee id is not set.\n\n"
            "Regards,\n"
            "MS Emp Per Bot"
        )
        datestamp = datetime.now().strftime("%Y-%m-%d")
        subject = f"MS EMP PER Notification for '{pc_name}' on '{datestamp}'."
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=SEND_EMAIL_TO,
            subject=subject,
            plain_text_content=content,
        )

        response: Any = sg.send(message)
        status_code: int = response.status_code
        info(f"Email sent to {SEND_EMAIL_TO}.")
        info(f"Email response status code: {status_code}")
        return None
    except Exception as e:
        error(f"`send_email` function failed: {e}")
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        return None


def post_version() -> None:
    # info(f"Version Post function running on thread {threading.current_thread()}")
    try:
        global __version__, VERSION_ENDPOINT
        version = __version__
        quanta = {"version": version, "org_id": 1}
        response = requests.post(
            url=VERSION_ENDPOINT,
            headers=return_headers(),
            timeout=VERSION_TIMEOUT,
            json=quanta,
        )
        sc: int = response.status_code
        message = response.text
        info("VERSION FUNCTION")
        info(f"Status Code: {sc}")
        info(f"Status Message: {message}")
        return None
    except Exception as e:
        error(f"`post_version` function failed: {e}")
        return None


def logger(log_entry: LogEntry) -> int:
    try:
        global log_file_path
        # Two step verification of logs
        if verify_log_correctness(log_entry) is False:
            return -1
        try:
            encrypted_log = f.encrypt(bytes(json.dumps(log_entry), "utf-8"))
        except Exception as e:
            raise Exception(f"Failed to encrypt data: {e}")
            # this log entry will not be written to log file
        with open(log_file_path, "ab") as log_file:
            log_file.write(b"ENC" + encrypted_log + b"\n")
            # Entry successfully logged
        return 0
    except Exception as err:
        error(f"`logger` function failed: {err}")
        error(f"The Log entry was: {json.dumps(log_entry, indent=2)}")
        return -1


def get_pc_name() -> str:
    try:
        pc_name = socket.getfqdn()
        return pc_name
    except Exception as e:
        error(f"`get_pc_name` function failed: {e}")
        return ""


# TODO: just return a string
# make changes in places that call this function.
def get_utc_time() -> Tuple[Exception | None, str]:
    try:
        utc_now: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return None, utc_now
    except Exception as err:
        return err, ""


def get_filename_safe_utc_time():
    utc_now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return utc_now


def generate_uuid() -> str:
    return str(uuid.uuid4())


def calculate_time_difference(start_time: str, end_time: str) -> int:
    try:
        if start_time == "" or end_time == "":
            return 0
        start_datetime = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_datetime = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        time_difference = end_datetime - start_datetime
        return int(time_difference.total_seconds())
    except Exception as err:
        error(f"`calculate_time_difference` function failed: {err}")
        return -1


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_ulong)]


def get_idle_time() -> int:
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        seconds = int(millis / 1000.0)
        return seconds
    except Exception as err:
        critical(f"`get_idle_time` function failed: {err}")
        return -1


def is_inactive() -> bool:
    if get_idle_time() > IDLE_THRESHOLD:
        return True
    else:
        return False


def is_screen_locked() -> bool:
    try:
        processes: Iterator[Process] = psutil.process_iter(["pid", "name"])
        for proc in processes:
            if proc.name() == "LogonUI.exe":
                print(proc.name())
                return True
        return False
    except Exception as err:
        print(f"`is_screen_locked` function failed: {err}")
        return False


def lock_windows_screen() -> bool:
    try:
        ctypes.windll.user32.LockWorkStation()
        return True
    except Exception as err:
        error(f"`lock_windows_screen` function failed: {err}")
        return False


def get_active_window() -> Tuple[Exception | None, str, str, int]:
    try:
        window = GetForegroundWindow()
        title = GetWindowText(window)
        _, pid = GetWindowThreadProcessId(window)
        if psutil.pid_exists(pid):
            process = psutil.Process(pid=pid)
            process_name: str = process.name()
            return None, process_name, title, pid
        else:
            print(f"PID does not exists: {pid} with title: {title}")
            return None, IDLE_APPLICATION_NAME, IDLE_APPLICATION_NAME, 0
    except Exception as err:
        return err, "", "", -1


def compress_image(image_path: str, quality: int) -> int:
    try:
        image = Image.open(image_path)
        image.save(fp=image_path, format="JPEG", optimize=True, quality=quality)
        return 0
    except Exception as err:
        error(f"`compress_image` function failed: {err}")
        return -1


def verify_user_settings(user_settings: List[Any]) -> bool:
    try:
        if not isinstance(user_settings, list):
            return False
        for setting in user_settings:
            if not isinstance(setting, dict) or len(setting) != 1:
                return False
            _, value = list(setting.items())[0]
            # Using list() to create a copy instead of modifying original settings
            if not isinstance(value, dict):
                return False
            required_keys_per_setting = {"is_active", "interval", "quality"}
            if not required_keys_per_setting.issubset(value):
                return False
        return True
    except Exception as err:
        error(f"`verify_user_settings` function failed: {err}")
        return False


def grab_webcam() -> None | Exception:
    try:
        global global_user_settings, USER_LOGIN_ID, WC_FOLDER
        correct_settings = verify_user_settings(user_settings=global_user_settings)
        if correct_settings is False:
            error("Settings were of incorrect format!")
            error(f"Incorrectly formatted settings: {global_user_settings}")
            return None
        if global_user_settings[1]["webcam"]["is_active"] is not True:
            info(
                "Webcam Functionality is off in user settings --> Not capturing webcam"
            )
            return None
        wc_quality: int = int(global_user_settings[1]["webcam"]["quality"])
        cap = cv2_VideoCapture(0)
        if cap.isOpened():
            info("Webcam is present on the system.")
            _, frame = cap.read()
            cap.release()
            uuid_str = generate_uuid()
            utc_time = get_filename_safe_utc_time()
            wc_folder = WC_FOLDER
            wc_file_path = os.path.join(
                wc_folder, f"{uuid_str}_{utc_time}_{USER_LOGIN_ID}.jpg"
            )
            cv2_imwrite(wc_file_path, frame)
            compression_status = compress_image(
                image_path=wc_file_path, quality=wc_quality
            )
            if compression_status == 0:
                return None  # Successfully compressed and saved
            if os.path.exists(wc_file_path):
                info(f"Removing {wc_file_path}")
                os.remove(wc_file_path)
                info("Saving uncompressed version")
                cv2_imwrite(wc_file_path, frame)
                info("Saved uncompressed version")
                return None
            else:
                error(f"No such file for webcam image: {wc_file_path}")
                return None
        else:
            info("No webcam was found on the system.")
            return None
    except Exception as err:
        return err


# TODO: check if compression for webcam and screenshots is working properly
def grab_screen() -> None | Exception:
    try:
        global global_user_settings, SS_FOLDER
        correct_settings = verify_user_settings(user_settings=global_user_settings)
        if correct_settings is False:
            error("Settings were of incorrect format!")
            error(f"Incorrectly formatted settings: {global_user_settings}")
            return None
        if not global_user_settings[0]["screenshot"]:
            return None
        if not global_user_settings[0]["screenshot"]["is_active"]:
            info("Screenshot Functionality is off --> Not capturing screenshot")
            return None
        quality: int = int(global_user_settings[0]["screenshot"]["quality"])
        uuid_str = generate_uuid()
        utc_time = get_filename_safe_utc_time()
        ss_folder = SS_FOLDER
        # if not os.path.exists(SS)
        ss_file_path = os.path.join(
            ss_folder, f"{uuid_str}_{utc_time}_{USER_LOGIN_ID}.jpg"
        )
        print(1)
        screenshot = ImageGrab.grab(all_screens=True)
        print(2)
        # FIXME: screenshot not working
        try:
            screenshot.save(fp=ss_file_path)
        except Exception as errr:
            error(f"Failed to save screenshot at `{ss_file_path}`: {errr}")
            return errr
        print(3)
        info(f"Screenshot saved: {ss_file_path}")
        compression_status = compress_image(image_path=ss_file_path, quality=quality)
        if compression_status == 0:
            return None  # Successfully compressed and saved
        if os.path.exists(ss_file_path):
            info(f"Removing screenshot: {ss_file_path}")
            os.remove(ss_file_path)
            info("Saving uncompressed screenshot")
            screenshot.save(fp=ss_file_path)
            return None
        else:
            error(f"No such file for screenshot exists: `{ss_file_path}`")
            return None
    except Exception as err:
        error(f"`grab_screen` failed: {err}")
        return err


def send_ss_and_delete() -> None:
    info("Starting to send screenshots")
    global USER_LOGIN_ID, SCREENSHOT_ENDPOINT, SEND_SS_LIMIT, SS_FOLDER
    info(f"Screenshot URL endpoint: {SCREENSHOT_ENDPOINT}")
    headers = return_headers()
    info(f"JWT TOKEN: {global_jwt}")
    if not os.path.isdir(SS_FOLDER):
        return None
    try:
        files_processed: int = 0
        for file in os.listdir(SS_FOLDER):
            if file.endswith(".jpg"):
                info(f"Trying to send {file}")
                file_path = os.path.join(SS_FOLDER, file)

                with open(file_path, "rb") as imgf:
                    imgfile = {"image": (file, imgf, "image/jpeg")}
                    response = requests.post(
                        url=SCREENSHOT_ENDPOINT,
                        headers=headers,
                        files=imgfile,
                        timeout=TIMEOUT_FOR_SENDING_SCREENSHOT,
                    )

                    info(f"Response: {response}")
                    info(f"Response Message: {response.text}")

                    imgf.close()  # Close before deleting image necessary

                    if response.status_code // 100 == 2:
                        info(f"Image {file} sent successfully.")
                        os.remove(file_path)
                        files_processed += 1
                        if files_processed >= SEND_SS_LIMIT:
                            info(f"{files_processed} files processed.")
                            info("Stopping further processing")
                            return
                    else:
                        error(
                            f"Failed to send image: {file}. Status Code: {response.status_code}"
                        )
                        error("Retruning from the function to prevent blocking")
                        return  # Hence if one file upload fails, the for loop will not
                        # block the execution of the program
        return None
    except Exception as e:
        error(f"`send_ss_and_delete` function failed: {e}")


def send_wc_and_delete():
    info("Starting to send webcam images")
    global USER_LOGIN_ID, WEBCAM_ENDPOINT, WC_FOLDER
    info(f"Webcam URL endpoint: {WEBCAM_ENDPOINT}")
    headers = return_headers()
    info(f"JWT TOKEN: {global_jwt}")
    if not os.path.isdir(WC_FOLDER):
        return None
    try:
        files_processed: int = 0
        for file in os.listdir(WC_FOLDER):
            if file.endswith(".jpg"):
                info(f"Trying to send {file}")
                file_path = os.path.join(WC_FOLDER, file)
                with open(file_path, "rb") as imgf:
                    imgfile = {"image": (file, imgf, "image/jpeg")}
                    response = requests.post(
                        url=WEBCAM_ENDPOINT,
                        headers=headers,
                        files=imgfile,
                        timeout=TIMEOUT_FOR_SENDING_WEBCAM,
                    )
                    info(f"Response: {response}")
                    info(f"Response Message: {response.text}")

                    imgf.close()  # Close before deleting image necessary

                    if response.status_code // 100 == 2:
                        info(f"Image {file} sent successfully.")
                        os.remove(file_path)
                        files_processed += 1
                        if files_processed >= SEND_WC_LIMIT:
                            info(f"{files_processed} files processed.")
                            info("Stopping further processing")
                            return
                    else:
                        error(
                            f"Failed to send image: {file}. Status Code: {response.status_code}"
                        )
                        return  # No need to try sending other images in the folder
    except Exception as e:
        error(f"`send_wc_and_delete` function failed: {e}")
        return e


def get_url_firefox(window_title: str, pid: int) -> Tuple[Exception | None, str]:
    try:
        debug("Trying to fetch firefox URL")
        for profile in FirefoxProfile.get_profiles():
            recovery_data = profile.get_recovery_data()
            if recovery_data is None:
                continue
            for window in recovery_data.windows:
                for tab in window.tabs:
                    if tab.title in window_title:
                        info(f"Last Accessed Tab: {tab.last_accessed}")
                        info(f"Tab URL: {tab.url}")
                        url = str(tab.url)
                        if validate_url(url=url):
                            return None, url
                        else:
                            return None, ""
        return None, ""
    except Exception as e:
        return e, ""


@lru_cache(maxsize=10)
def get_url_edge(window_title: str, pid: int) -> Tuple[Exception | None, str]:
    try:
        app = Application(backend="uia").connect(process=pid)
        dlg = app.top_window()
        wrapper = dlg.child_window(title="App bar", control_type="ToolBar")
        url = wrapper.descendants(control_type="Edit")[0]
        url = url.get_value()
        url = str(url)
        if validate_url(url=url):
            return None, url
        else:
            return None, ""
    except Exception as e:
        return e, ""


@lru_cache(maxsize=10)
def get_url_chrome(window_title: str, pid: int) -> Tuple[Exception | None, str]:
    try:
        start_t = time.time()
        app = Application(backend="uia", allow_magic_lookup=True).connect(process=pid)
        dlg = app.top_window()
        title = "Address and search bar"
        url = dlg.child_window(
            title=title, control_type="Edit", top_level_only=True
        ).get_value()
        url = str(url)
        # err, is_valid_url = validate_url(url=url)
        # if validate_url(url=url):
        #     return
        end_t = time.time()
        time_taken = end_t - start_t

        debug(f"{window_title}  -->  {time_taken}")

        if validate_url(url=url):
            return None, url
        else:
            return None, ""
    except Exception as e:
        return e, ""


def is_internet_accessible() -> bool:
    try:
        response = requests.get("http://google.com", timeout=3)
        if response.status_code // 100 == 2:
            return True
        else:
            return False
    except Exception as err:
        error(f"`is_internet_accessible` function failed: {err}")
        return False


def is_valid_localhost(address: str) -> bool:
    try:
        pattern = (
            r"^(?:(?:http|https)://)?(?:localhost|127\.0\.0\.1)(?::\d{1,5})?(?:\/.*)?$"
        )
        if re.match(pattern, address):
            return True
        else:
            return False
    except Exception as err:
        error(f"`is_valid_localhost` function failed: {err}")
        return False


def validate_url(url: str) -> bool:
    try:
        info("Validating URL")
        if is_valid_localhost(address=url):
            info(f"Valid localhost address: {url}")
            return True
        if (
            validators.url(url)
            or validators.domain(url)
            or validators.domain(url.split("/")[0])
            or validators.ipv4(url)
            or validators.ipv6(url)
            or validators.ipv4(url.split(":")[0])
        ):
            info(f"URL Validation Succeeded: {url}")
            return True
        else:
            error(f"URL Validation Failed: {url}")
            return False
    except Exception as e:
        error(f"`validate_url` function failed: {e}")
        return False


def get_browser_url(
    window_title: str, browser_name: str, pid: int
) -> Tuple[Exception | None, str]:
    try:
        if pid < 1:
            return None, ""
        if browser_name == "firefox.exe":
            err, url = get_url_firefox(window_title=window_title, pid=pid)
            if err is not None:
                error(f"`get_url_firefox` function failed: {err}")
                return err, ""
            else:
                info(f"{url}")
                return None, url
        elif browser_name == "msedge.exe":
            err, url = get_url_edge(window_title=window_title, pid=pid)
            if err is not None:
                error(f"`get_url_edge` function failed: {err}")
                return err, ""
            else:
                return None, url
        elif browser_name == "chrome.exe":
            # info(f"LRU CACHE: {get_url_chrome.cache_info()}")
            # check in cache
            err, url = get_url_chrome(window_title=window_title, pid=pid)
            # put in cache title --> url
            if err is not None:
                error(f"`get_url_chrome` function failed: {err}")
                return err, ""
            else:
                return None, url
        elif browser_name == "brave.exe":
            err, url = get_url_chrome(window_title=window_title, pid=pid)
            if err is not None:
                error(f"`get_url_chrome` function failed for brave browser: {err}")
                return err, ""
            else:
                return None, url
        else:
            return None, ""
    except Exception as err:
        return err, ""


def load_user_settings() -> Union[Exception, None]:
    info("Loading user settings...")
    global settings_file_path, global_user_settings
    try:
        with open(settings_file_path) as settings_file:
            content = settings_file.read()
            global_user_settings = json.loads(content)
            correct_settings = verify_user_settings(global_user_settings)
            if correct_settings:
                info("User settings object verification succeeded.")
            else:
                info("User settings object verification failed.")
            info(
                "USER SETTINGS LOADED FROM FILE:\n"
                f"{json.dumps(global_user_settings, indent=2)}"
            )
            return None
    except Exception as err:
        error(f"`load_user_settings` function failed: {err}")
        return err


def fetch_user_settings() -> Union[Exception, None]:
    try:
        global USER_SETTINGS_ENDPOINT, global_user_settings, USER_LOGIN_ID
        global settings_file_path
        info(
            f"Fetch User Settings function running on thread {threading.current_thread()}"
        )
        if not is_remote_api_accessible():
            raise Exception("Remote API was inaccessible.")
        jwt_status: int = validate_jwt_token()
        if jwt_status < 0:
            raise Exception(
                "JWT Verification function failed -> Not fetching user settings."
            )
        if jwt_status // 100 != 2:
            raise Exception(f"JWT Verification failed with status code: {jwt_status}")
        headers = return_headers()
        info("Fetching User Settings...")
        response = requests.get(
            url=USER_SETTINGS_ENDPOINT,
            headers=headers,
            timeout=TIMEOUT_FOR_FETCHING_USER_SETTINGS,
        )
        info(f"Response received: {response}")
        sc = response.status_code
        info(f"Status Code [USER SETTINGS]: {sc}")
        if sc == 200:
            info(f"Response JSON from API: {response.json()}")
            response_settings = response.json()
            if isinstance(response_settings, list):
                global_user_settings = response.json()
                with open(settings_file_path, "w+") as settings_file:
                    settings_file.write(json.dumps(global_user_settings, indent=2))
                    info("User settings fetched and saved in local file.")
                # DEBUG
                err = load_user_settings()
                return None
            if isinstance(response_settings, dict):
                raise Exception("Incorrect format of user settings sent by remote API")
            return None
        else:
            raise Exception(
                f"Fetch user settings API was inaccessible. Status Code: {sc}"
            )
    except Exception as e:
        err = load_user_settings()
        if err is not None:
            error(f"`load_user_settings` function failed: {err}")
        return e


def validate_jwt_token() -> int:
    global global_jwt, JWT_TOKEN_ENDPOINT, API_KEY, USER_LOGIN_ID, JWT_TOKEN_TIMEOUT
    try:
        headers = return_headers()
        # json_data = {"user_id": USER_LOGIN_ID, "org_id": 1}
        response = requests.get(
            url=JWT_TOKEN_ENDPOINT,
            headers=headers,
            timeout=JWT_TOKEN_TIMEOUT,
            # json=json_data,
        )
        sc: int = response.status_code
        response_message = response.json()
        print(sc)
        print(response_message)
        info(f"Response from JWT Route: {json.dumps(response_message, indent=2)}")
        info(f"Status Code [JWT VERIFICATION]: {sc}")
        if sc == 200:
            info("Connection with JWT Verification API was successful.")
            info("JWT Token was already valid!")
        elif sc == 202:
            info("JWT Token Refreshed successfully!")
            quanta = response.json()
            global_jwt = quanta["token"]
            info(f"Refreshed JWT: {global_jwt}")
        elif sc == 406:
            info("User not found in SQL User Table")
        else:
            error("Connection with JWT Verification API was unsuccessful.")
        return sc
    except Exception as err:
        error(f"`validate_jwt_token` function failed: {err}")
        return -1


def count_lines(file_path: str) -> int:
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            return len(lines)
    except Exception as e:
        error(f"`count_lines` function failed: {e}")
        return -1


def sent_request_to_server_successfully(
    log_lines: List[Dict[str, Union[str, int]]],
) -> bool:
    try:
        global global_jwt, SERVER_POST_LOGS_ENDPOINT, SEND_LOGS_TIMEOUT
        headers = return_headers()

        response = requests.post(
            url=SERVER_POST_LOGS_ENDPOINT,
            headers=headers,
            json=log_lines,
            timeout=SEND_LOGS_TIMEOUT,
        )

        info(f"Response Message[SEND LOGS]: {json.dumps(response.json(), indent=2)}")
        info(f"Status Code [SEND LOGS]: {response.status_code}")

        return response.status_code // 100 == 2
    except Exception as e:
        error(f"`send_request_to_api` function failed: {e}")
        return False


# TODO: this func is computationally expensive. Try optimizing.
def delete_incorrect_log_entries(file_path: str, line_numbers: list[int]) -> None:
    try:
        with open(file_path, "r+") as file:
            content = file.readlines()
            new_content: list[str] = []
            file.seek(0)
            for i, line in enumerate(content):
                if i in line_numbers:
                    info(
                        f"Found line to delete in file: `{os.path.basename(file_path)}`. Line Number: {i}"
                    )
                else:
                    new_content.append(line)
            file.seek(0)
            file.writelines(new_content)
            file.truncate()
            return None
    except Exception as err:
        error(f"`delete_incorrect_log_entries` function failed: {err}")


def delete_n_lines_from_start(file_path: str, n: int) -> int:
    try:
        with open(file_path, "r+") as file:
            content = file.readlines()
            file.seek(0)
            file.writelines(content[n:])
            file.truncate()
            return 0
    except Exception as err:
        error(f"`delete_sent_logs` function failed: {err}")
        return -1


def verify_datetime_format(datetime_str: str | None | int) -> bool:
    try:
        if datetime_str is None:
            return False
        if isinstance(datetime_str, int):
            return False
        datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError as ve:
        error(f"{ve}")
        return False
    except Exception as err:
        error(f"`verify_datetime_format` function failed: {err}")
        return False


def verify_log_correctness(log_entry: LogEntry) -> bool:
    try:
        if (
            not log_entry["user_id"]
            or not log_entry["time_spent"]
            or not verify_datetime_format(log_entry["start_time"])
            or not verify_datetime_format(log_entry["end_time"])
            or not log_entry["application_name"]
            or not log_entry["window_title"]
        ):
            return False
        else:
            return True
    except Exception as err:
        error(f"`verify_log_correctness` function failed: {err}")
        return False


def form_log_packet(num_lines_to_send: int):
    log_lines: list[dict[str, str | int]] = []
    incorrect_log_entry_line_numbers: list[int] = []
    try:
        with open(log_file_path, "rb") as logf:
            # lines = logf.readlines()[:num_lines_to_send]
            # the following is more efficient than reading the entire file:
            lines = [logf.readline() for _ in range(num_lines_to_send)]
            for i, line in enumerate(lines):
                try:
                    if line.startswith(b"ENC"):
                        decrypted_log = f.decrypt(line[3:])
                        decoded_log = decrypted_log.decode("utf-8")
                        decoded_log_dict = json.loads(decoded_log)
                        if verify_log_correctness(decoded_log_dict):
                            info("Log was correct")
                            log_lines.append(decoded_log_dict)
                        else:
                            error(f"Incorrect log entry found at line number: {i}")
                            error(f"Line: {line}")
                            incorrect_log_entry_line_numbers.append(i)
                            continue
                    else:
                        error(f"Incorrect log entry found at line number: {i}")
                        error(f"Line: {line}")
                        incorrect_log_entry_line_numbers.append(i)
                except Exception as decrypt_error:
                    error(f"Error decrypting line {i}: {str(decrypt_error)}")
                    incorrect_log_entry_line_numbers.append(i)
                    continue
            delete_incorrect_log_entries(
                file_path=log_file_path, line_numbers=incorrect_log_entry_line_numbers
            )
        return None, log_lines
    except Exception as e:
        return e, None


def is_remote_api_accessible() -> bool:
    global SERVER_STATUS_ENDPOINT, SERVER_STATUS_TIMEOUT
    try:
        response = requests.get(
            url=SERVER_STATUS_ENDPOINT, timeout=SERVER_STATUS_TIMEOUT
        )
        if response.status_code // 100 == 2:
            print(response.json())
            return True
        else:
            return False
    except Exception as e:
        error(f"`is_remote_api_accessible` function failed: {e}")
        return False


def send_logs() -> None:
    info(f"Send Logs function running on thread {threading.current_thread()}")
    global LOG_SENDING_LIMIT, log_file_path
    try:
        if not is_remote_api_accessible():
            error("Remote API was inaccessible. Not sending logs.")
            return None

        num_lines_log = count_lines(log_file_path)
        # TODO: maybe decide a minimum number of log lines to send
        # This would reduce number of hits to the server and
        # thus the server would be able to handle more simultaneous
        # users
        if num_lines_log < 1:
            info("No logs to send. Skipping log sending.")
            return None

        num_lines_to_send: int = min(num_lines_log, LOG_SENDING_LIMIT)
        starttime: float = time.time()  # Start timer to measure log sending time

        err, log_lines = form_log_packet(num_lines_to_send)
        if err is not None:
            error(f"`form_log_packet` function failed: {err}")
            return
        else:
            # log packet was formed successfully
            if not log_lines:
                return
            if len(log_lines) < 1:
                return

        info("LOGS TO BE SENT")
        info(json.dumps(log_lines, indent=2))

        if sent_request_to_server_successfully(log_lines=log_lines):
            del_status: int = delete_n_lines_from_start(
                file_path=log_file_path, n=len(log_lines)
            )
            if del_status == 0:
                info(
                    f"Logs sent successfully & {len(log_lines)} lines removed from logs"
                )
            endtime: float = time.time()
            exectime: float = endtime - starttime  # time to send logs
            info(f"Time Taken to send logs to the remote API: {exectime}")
        else:
            error("Failed to send logs")
    except Exception as e:
        error(f"`send_logs` function failed: {e}")


def make_appdata_filetree() -> int:
    global log_file_path, LOG_FILE_NAME, settings_file_path, SETTINGS_FILE_NAME
    global resource_consumption_log_file_path, RESOURCE_CONSUMPTION_LOG_FILE_NAME
    global SS_FOLDER, WC_FOLDER
    try:
        appdata = os.path.expandvars("%appdata%")
        diagnostics_folder = os.path.join(appdata, "MS-Diagnostics")
        screenshots_folder = SS_FOLDER
        webcam_folder = WC_FOLDER
        log_file = os.path.join(diagnostics_folder, LOG_FILE_NAME)
        resource_consumption_log_file_path = os.path.join(
            diagnostics_folder, RESOURCE_CONSUMPTION_LOG_FILE_NAME
        )
        settings_file = os.path.join(diagnostics_folder, SETTINGS_FILE_NAME)
        os.makedirs(diagnostics_folder, exist_ok=True)
        os.makedirs(screenshots_folder, exist_ok=True)
        os.makedirs(webcam_folder, exist_ok=True)
        if not os.path.exists(resource_consumption_log_file_path):
            with open(resource_consumption_log_file_path, "w"):
                pass
        open(log_file, "a").close()
        if not os.path.exists(settings_file):
            with open(settings_file, "w") as setf:
                setf.write("[]")
        else:
            open(settings_file, "a").close()
        log_file_path = log_file
        settings_file_path = settings_file
        return 0
    except Exception as err:
        error(f"`make_appdata_filetree` function failed: {err}")
        return -1


def generic_mailer(
    mail_content: str, subject: str, send_email_to: List[str], from_email: str
):
    try:
        message = Mail(
            from_email=from_email,
            to_emails=send_email_to,
            subject=subject,
            plain_text_content=mail_content,
        )
        response: Any = sg.send(message)
        status_code: int = response.status_code
        info(f"Email sent to {send_email_to}.")
        info(f"Email response status code: {status_code}")
        return None
    except Exception as err:
        error(f"`generic_mailer` function failed: {err}")
        return None


def mail_if_update_script_absent():
    try:
        global SEND_EMAIL_TO, FROM_EMAIL
        # TODO: change mail recepient email id
        temp_send_email_to = ["swarnim335@gmail.com"]
        script_path = os.path.join(
            os.path.expandvars("${programfiles(x86)}"),
            "MS-Diagnostics",
            "diagnostics-update.ps1",
        )
        if os.path.exists(script_path):
            info("The powershell update script exists!")
            return
        # The following code will only be executed if update script is absent:
        # Update script was not found -> Trigger Mail
        pc_name = get_pc_name()
        curtime: datetime = datetime.now()
        ds: str = curtime.strftime("%Y-%m-%d")
        ts: str = curtime.strftime("%Y-%m-%d_%H:%M:%S")
        subject: str = f"MS EMP PER Notification for `{pc_name}` dated {ds}"
        content = (
            "Hi,\n\n"
            "This is a system generated notification from MS Employee Performance Tool.\n\n"
            f"On the following computer '{pc_name}' the powershell update script was absent/deleted.\n\n"
            "No further action is needed since I auto-installed the update script on the computer."
            f"The update script was found to be absent on: {ts}.\n\n"
            "Regards,\n"
            "MS Emp Per Bot"
        )
        generic_mailer(
            mail_content=content,
            subject=subject,
            from_email=FROM_EMAIL,
            send_email_to=temp_send_email_to,
        )

        # After mailing, download the update script once again
        # so that manual intervention wont be necessary later
        update_update_script()
        return
    except Exception as err:
        error(f"`mail_if_update_script_absent` function failed: {err}")
        return


def get_blob_last_modified_datetime(file_url: str):
    try:
        response = requests.head(file_url)
        print(response.headers)
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


def get_blob_content_length(file_url: str):
    try:
        response = requests.head(file_url, timeout=5)
        if response.status_code // 100 != 2:
            return 0
        else:
            return int(response.headers.get("Content-Length", 0))
    except Exception as err:
        error(f"`get_blob_content_length` function failed: {err}")
        return -1


def update_update_exe():
    try:
        if not is_internet_accessible():
            info("No internet connection!")
            return None
        updater_name = "MS-Diagnostics-Updater.exe"
        pfx86 = os.path.expandvars("${programfiles(x86)}")
        project_folder = os.path.join(pfx86, "MS-Diagnostics")
        update_exe_path = os.path.join(project_folder, updater_name)
        blob_url_for_exe = emp_per_env.UPDATER_EXE_BLOB_URL
        if not os.path.exists(update_exe_path):
            info("Updater EXE was not found, downloading...")

            _ = utils.download_atomically(fp=update_exe_path, url=blob_url_for_exe)

        blob_file_size: int = get_blob_content_length(file_url=blob_url_for_exe)
        local_file_size: int = os.path.getsize(update_exe_path)

        local_last_mtime = datetime.fromtimestamp(
            os.path.getmtime(update_exe_path), tz=timezone.utc
        )
        remote_last_mtime = get_blob_last_modified_datetime(file_url=blob_url_for_exe)

        if not local_last_mtime:
            return None
        if not remote_last_mtime:
            return None

        if remote_last_mtime > local_last_mtime or local_file_size != blob_file_size:
            info(f"New update found for {updater_name}")
            # if exe is running, close exe
            while proc_utils.is_process_running(updater_name):
                proc_utils.kill_proc(updater_name)

            _ = utils.download_atomically(fp=update_exe_path, url=blob_url_for_exe)

        else:
            info("Updater EXE already upto date.")
            return None

    except Exception as err:
        error(f"`update_update_exe` function failed: {err}")
        return None


def update_update_script() -> None:
    try:
        if not is_internet_accessible():
            return None
        pfx86 = os.path.expandvars("${programfiles(x86)}")
        script_folder = os.path.join(pfx86, "MS-Diagnostics")
        script_path = os.path.join(script_folder, "diagnostics-update.ps1")
        blob_url = emp_per_env.UPDATER_PS1_BLOB_URL
        # TODO: download atomically?
        download_status = utils.download_atomically(fp=script_path, url=blob_url)

        # with requests.get(blob_url) as response:
        #     response.raise_for_status()
        #     with open(
        #         script_path, "w", encoding="utf-8", newline="\n"
        #     ) as update_script:
        #         update_script.write(response.text)
        if download_status:
            info("Script updated successfully")
        else:
            error("Failed to update update script")
        return None
    except Exception as err:
        error(f"`update_update_script` function failed: {err}")
        return None


def remove_url_prefix(url: str) -> str:
    try:
        resultant_url: str = url
        if url == "":
            return url
        prefixes = ("http://", "https://")
        for prefix in prefixes:
            if url == prefix or url.startswith(prefix):
                resultant_url = url[len(prefix) :]
                break
        if url.startswith("www."):
            resultant_url = url[len("www.") :]
        return resultant_url
    except Exception as err:
        error(f"`remove_url_prefix` function failed: {err}")
        return url


# To be called after removing `http(s)` prefixes
def get_domain_name(url: str) -> str:
    try:
        domain_name: str = ""
        split_url = url.split("/")
        domain_name = split_url[0]
        return domain_name
    except Exception as err:
        error(f"`get_domain_name` function failed: {err}")
        return url


def recheck_idle_time(start_time: str, end_time: str, kernel_idle_time: int) -> int:
    try:
        calc_idle_time = calculate_time_difference(start_time, end_time)
        if calc_idle_time < 0:
            return 0
        if kernel_idle_time == calc_idle_time:
            return kernel_idle_time
        else:
            return calc_idle_time
    except Exception as e:
        error(f"`recheck_idle_time` function failed: {e}")
        return 0


def chop_values(value: str | None, trim_len: int):
    try:
        if value is None:
            return ""
        return value[:trim_len]
    except Exception as err:
        error(f"`chop_values` function failed: {err}")
        return ""  # TODO: maybe return the input string instead?


def append_to_resource_consumption_log_file(
    log_file_path: str, entries: List[Dict[str, Any]]
) -> int:
    try:
        if len(entries) < 1:
            return 0
        if not os.path.exists(log_file_path):
            open(log_file_path, "w")
            pass
        with open(log_file_path, "a") as file:
            for entry in entries:
                entry = json.dumps(entry)
                file.write(entry + "\n")
            return 0
    except Exception as err:
        error(f"`append_to_resource_consumption_log_file` function failed: {err}")
        return -1


def form_resource_consumption_log_packet():
    try:
        global resource_consumption_log_file_path
        global RESOURCE_CONSUMPTION_MAX_LOGS_TO_SEND
        json_logs: List[Dict[str, Any]] = []
        incorrect_line_nums: List[int] = []

        if not os.path.exists(resource_consumption_log_file_path):
            return None

        num_lines_to_send = min(
            count_lines(resource_consumption_log_file_path),
            RESOURCE_CONSUMPTION_MAX_LOGS_TO_SEND,
        )
        with open(resource_consumption_log_file_path, "r+") as file:
            lines = [file.readline() for _ in range(num_lines_to_send)]
            for i, line in enumerate(lines):
                print(type(line))
                print(line)
                try:
                    entry: Dict[str, Any] = json.loads(line)
                except json.JSONDecodeError as jde:
                    error(
                        f"Incorrect resource consumption log found at line number: `{i + 1}`: {jde}"
                    )

                    incorrect_line_nums.append(i)
                    continue
                # print(entry)
                # TODO: delete line if that particular line causes exception?
                json_logs.append(entry)
            print(json.dumps(json_logs, indent=2))
            delete_incorrect_log_entries(
                file_path=resource_consumption_log_file_path,
                line_numbers=incorrect_line_nums,
            )
            return json_logs
    except Exception as err:
        error(f"`form_resource_consumption_log_packet` function failed: {err}")
        return None


def send_system_resource_consumption_logs() -> int:
    try:
        global RESOURCE_CONSUMPTION_ENDPOINT, resource_consumption_log_file_path
        headers = return_headers()

        if not is_remote_api_accessible():
            info("Remote API was inaccessible. Not sending resource consumption logs.")
            return -1

        json_logs: List[Dict[str, Any]] | None = form_resource_consumption_log_packet()
        if json_logs is None:
            info("No logs, skipping sending of logs.")
            return -1

        response = requests.post(
            url=RESOURCE_CONSUMPTION_ENDPOINT,
            headers=headers,
            json=json_logs,
            timeout=RESOURCE_CONSUMPTION_REQUEST_TIMEOUT,
        )

        num_logs_sent = len(json_logs)
        sc = response.status_code
        if sc // 100 != 2:
            error(
                f"Failed to send resource consumption logs to server.\nStatus Code: {sc}"
            )
            return -1
        else:
            info(
                f"Sent resource consumption logs successfully to server.\nStatus Code: {sc}"
            )
            del_status: int = delete_n_lines_from_start(
                file_path=resource_consumption_log_file_path,
                n=num_logs_sent,
            )
            if del_status == 0:
                info(
                    "Resource Consumption Logs sent successfully. "
                    f"`{num_logs_sent}` lines removed from logs"
                )
            return 0
    except Exception as err:
        error(f"`send_system_resource_consumption_logs` function failed: {err}")
        return -1


def make_resource_consumption_entries(
    pc_name: str, capture_time: str, **kwargs: Any
) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    try:
        for property_name, property_value in kwargs.items():
            print(f"{property_name}: {property_value}")
            obj: Dict[str, str] = {
                "property_name": property_name,
                "property_value": property_value,
                "start_time": capture_time,
                "pc_name": pc_name,
            }
            entries.append(obj)
        return entries
    except Exception as err:
        error(f"`make_resource_consumption_entries`: {err}")
        return entries


def capture_system_resource_consumption() -> int:
    try:
        global USER_LOGIN_ID
        # Capture Data
        info("Started capturing system resource consumption data.")
        cpu_percent: str = str(psutil.cpu_percent())
        ram_percent: str = str(psutil.virtual_memory()[2])
        network_status = psutil.net_io_counters()
        bytes_sent = str(network_status.bytes_sent)
        bytes_received = str(network_status.bytes_recv)
        c_drive_usage_percent = str(psutil.disk_usage("C:\\").percent)
        # TODO: add bytes sent, bytes received,
        # TODO: add disk usage
        _, capture_time = get_utc_time()
        pc_name = get_pc_name()
        info("Finished capturing system resource consumption data.")

        if pc_name is None and USER_LOGIN_ID == "None":
            critical("Both pc_name and user_login_id were found to be none!")
            return -1

        # Make entries
        entries: List[Dict[str, Any]] = []
        entries = make_resource_consumption_entries(
            pc_name=pc_name,
            capture_time=capture_time,
            ram_percent=ram_percent,
            cpu_percent=cpu_percent,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            c_drive_usage_percent=c_drive_usage_percent,
        )

        # Append string to a log file
        append_to_resource_consumption_log_file(
            resource_consumption_log_file_path, entries
        )
        info("Appended entry to resource consumption log file.")
        return 0
    except Exception as err:
        error(f"`capture_system_resource_consumption` function failed: {err}")
        return -1


def send_mail_if_log_lines_more_than_1000():
    if not is_remote_api_accessible():
        return None
    global log_file_path
    n = count_lines(file_path=log_file_path)
    if n >= 1000:
        info(f"Log file had `{n}` lines. Sending mail...")
        datestamp = datetime.now().strftime("%Y-%m-%d")
        to_mail = SEND_EMAIL_TO
        pc_name = get_pc_name()
        from_email = FROM_EMAIL
        subject = f"Employee Performance System Notification on `{datestamp}`"
        content = (
            "Hello,\n\nThis is a system generated notification for `Employee Performance System`.\n"
            f"The system `{pc_name}` has more than 1000 logs in the log file.\n\n"
            "Regards,\nEmployee Performance System"
        )
        generic_mailer(
            mail_content=content,
            subject=subject,
            send_email_to=to_mail,
            from_email=from_email,
        )
    else:
        info("Log file had lines within limit.")
        return


def run_threaded(job_function: Callable, job_name: str) -> None:
    try:
        job_thread = threading.Thread(target=job_function, name=job_name)
        job_thread.start()
    except threading.ThreadError as te:
        error(f"`run_threaded` function failed: {te}")
        error(f"Failed to start `{job_name}` in a separate thread")


def monitor_active_window() -> Exception:
    global global_user_settings, USER_LOGIN_ID
    info("Starting Monitoring...")
    status_code: int = validate_jwt_token()
    if status_code < 0:
        error("JWT Verification Function failed.")
    try:
        previous_title = start_time = end_time = ""
        previous_active_window = url = url_name = ""
        log_entry: LogEntry
        screenshot_timer_start = datetime.now()
        webcam_timer_start = datetime.now()
        total_idle_time: int = 0

        # schedule.every().day.at("10:30").do(run_threaded, send_email)
        # schedule.every().day.at("14:30").do(run_threaded, send_email)
        # schedule.every(FETCH_USER_SETTINGS_EVERY).seconds.do(run_threaded, fetch_user_settings)
        # schedule.every(SEND_LOGS_AFTER).seconds.do(run_threaded, send_logs)
        # schedule.every(VERSION_POST_SCHEDULE).seconds.do(run_threaded, post_version)

        # schedule.every(CHECK_LOG_FILE_LENGTH_EVERY).seconds.do(
        #     lambda: run_threaded(
        #         send_mail_if_log_lines_more_than_1000, "SendMailIfLogLinesMoreThan1000"
        #     )
        # )

        schedule.every(SEND_RESOURCE_CONSUMTION_LOGS_EVERY).seconds.do(
            lambda: run_threaded(
                send_system_resource_consumption_logs,
                "CaptureSystemResourceConsumption",
            )
        )
        schedule.every(CAPTURE_RESOURCE_CONSUMPTION_EVERY).seconds.do(
            capture_system_resource_consumption
        )

        schedule.every().day.at("10:30").do(
            lambda: run_threaded(send_email, "SendEmailJob1")
        )
        schedule.every().day.at("14:30").do(
            lambda: run_threaded(send_email, "SendEmailJob2")
        )
        schedule.every(FETCH_USER_SETTINGS_EVERY).seconds.do(
            lambda: run_threaded(fetch_user_settings, "FetchUserSettingsJob")
        )

        schedule.every(SEND_LOGS_AFTER).seconds.do(
            lambda: run_threaded(send_logs, "SendLogsJob")
        )

        schedule.every(VERSION_POST_SCHEDULE).seconds.do(
            lambda: run_threaded(post_version, "PostVersionJob")
        )

        # schedule.every(UPDATE_SCRIPT_PRESENCE_CHECK_DURATION).seconds.do(
        #     lambda: run_threaded(
        #         mail_if_update_script_absent, "MailIfUpdateScriptPresent"
        #     )
        # )
        info("All tasks scheduled...")

        while True:
            is_screen_locked()
            # info(f"Number of active threads: {threading.active_count()}")
            if start_time == "":
                err, start_time = get_utc_time()
                if err is not None:
                    critical(f"`get_utc_time` function failed: {err}")
                    continue
            if not os.path.exists(log_file_path):
                info("Log file was not found. Creating...")
                if make_appdata_filetree() < 0:
                    error("Could not create log file.")
                else:
                    info("Log file created successfully.")
            else:
                pass  # log file exists

            # Scheduled Jobs
            schedule.run_pending()

            # SCREENSHOT CAPTURE TIMER
            if global_user_settings and global_user_settings[0]["screenshot"]:
                screenshot_timer_current = datetime.now()
                screenshot_interval = int(
                    global_user_settings[0]["screenshot"]["interval"]
                )
                screenshot_is_active = global_user_settings[0]["screenshot"][
                    "is_active"
                ]
                if screenshot_is_active:
                    if screenshot_timer_current - screenshot_timer_start >= timedelta(
                        seconds=screenshot_interval
                    ):
                        info("Time to take a screenshot")
                        err = grab_screen()
                        if err is not None:
                            error(f"`grab_screen` function failed: {err}")
                        send_ss_and_delete()
                        screenshot_timer_start = datetime.now()
                    else:
                        timediff = (
                            screenshot_timer_current - screenshot_timer_start
                        ).total_seconds()
                        info(
                            f"TIME REMAINING FOR NEXT SCREENSHOT: {screenshot_interval - timediff}"
                        )

            # WEBCAM CAPTURE TIMER
            if global_user_settings and global_user_settings[1]["webcam"]:
                webcam_is_active = global_user_settings[1]["webcam"]["is_active"]
                if webcam_is_active:
                    webcam_timer_current = datetime.now()
                    webcam_interval = int(global_user_settings[1]["webcam"]["interval"])
                    if webcam_timer_current - webcam_timer_start >= timedelta(
                        seconds=webcam_interval
                    ):
                        info("Time to take grab webcam")
                        err = grab_webcam()
                        if err is not None:
                            error(f"`grab_webcam` function failed: {err}")
                        send_wc_and_delete()
                        webcam_timer_start = datetime.now()
                    else:
                        timediff = (
                            webcam_timer_current - webcam_timer_start
                        ).total_seconds()
                        info(
                            f"TIME REMAINING FOR NEXT WEBCAM: {webcam_interval - timediff}"
                        )

            if is_inactive():
                total_idle_time = get_idle_time()
                # TODO: check if screen locking functionality
                # is on in user settings
                # If on, then carry out the locking logic
                # else continue.
                if total_idle_time > SCREEN_LOCK_TIME:
                    if is_screen_locked():
                        app_name = IDLE_APPLICATION_NAME
                        previous_title = "Windows Default Lock Screen"
                        continue
                    else:
                        lock_screen_status = lock_windows_screen()
                        if lock_screen_status is True:
                            info("Screen locked successfully.")
                        else:
                            info("Screen could not be locked.")
                else:
                    pass
            else:
                if total_idle_time > 0:
                    err, end_time = get_utc_time()
                    if err is not None:
                        critical(f"`get_utc_time` function failed: {err}")
                        # TODO: do something about the error?
                    rechecked_idle_time = recheck_idle_time(
                        start_time, end_time, total_idle_time
                    )
                    app_name = IDLE_APPLICATION_NAME
                    window_title = chop_values(previous_title, WINDOW_TITLE_MAX_LENGTH)
                    if start_time == "":
                        err, start_time = get_utc_time()
                        if err is not None:
                            critical(f"`get_utc_time` function failed: {err}")
                            # TODO: do something about the error?
                    if start_time != "" and end_time != "":
                        log_entry: LogEntry = {
                            "user_id": USER_LOGIN_ID,
                            "start_time": start_time,
                            "application_name": app_name,
                            "window_title": window_title,
                            "url": "",
                            "url_name": "",
                            "end_time": end_time,
                            "time_spent": rechecked_idle_time,
                        }
                        # TODO: add idle time threshold
                        if rechecked_idle_time > MAX_IDLE_TIME_TO_LOG:
                            info(
                                f"IDLE TIME entry has time spent more than: {MAX_IDLE_TIME_TO_LOG} seconds. Not logging."
                            )
                            pass
                        else:
                            logger_status = logger(log_entry)
                            if logger_status == 0:
                                info("Log saved successfully!")
                                info(json.dumps(log_entry, indent=2))
                                info("Idle Time Logged!")
                    total_idle_time = 0
                    err, start_time = get_utc_time()
                    if err is not None:
                        critical(f"`get_utc_time` function failed: {err}")
                        # TODO: do something about the error?

            err, active_window, title, pid = get_active_window()
            if err is not None:
                critical(f"`get_active_window` function failed: {err}")
                continue  # could not get process name, title, pid
            # TODO
            if previous_title != title and title != "":
                log_entry: LogEntry = {
                    "user_id": USER_LOGIN_ID,
                    "start_time": start_time,
                    "application_name": chop_values(
                        previous_active_window, APPLICATION_NAME_MAX_LENGTH
                    ),
                    "window_title": chop_values(
                        previous_title, WINDOW_TITLE_MAX_LENGTH
                    ),
                    "url": "",
                    "url_name": "",
                    "end_time": "",
                    "time_spent": 0,
                }
                if url:
                    url_name = chop_values(url_name, URL_NAME_MAX_LENGTH)
                    log_entry["url"] = url
                    log_entry["url_name"] = url_name
                    log_entry["application_name"] = url_name
                    url = ""
                    url_name = ""

                info(f"Title: {title}")
                info(f"Active Window: {active_window}")
                info("Trying to fetch url")
                err, url = get_browser_url(title, active_window, pid)
                if err is not None:
                    error(f"`get_browser_url`: function failed: {err}")
                    # TODO: maybe use continue?
                else:
                    url = remove_url_prefix(url)
                    url_name = get_domain_name(url)

                # if previous_title is not None and previous_active_window is not None:
                err, end_time = get_utc_time()
                if err is not None:
                    critical(f"`get_utc_time` function failed: {err}")
                    # TODO: do something about the error?
                log_entry["end_time"] = end_time
                time_spent = calculate_time_difference(start_time, end_time)
                if time_spent < 0:
                    continue
                else:
                    log_entry["time_spent"] = time_spent
                    logger_status = logger(log_entry)
                    if logger_status == 0:
                        info("Log saved successfully!")
                        info(json.dumps(log_entry, indent=2))
                # If conditon ends
                err, start_time = get_utc_time()
                if err is not None:
                    critical(f"`get_utc_time` function failed: {err}")
                    # TODO: do something about the error?
                previous_title = title
                previous_active_window = active_window
            time.sleep(MONITOR_WINDOW_EVERY)
    except Exception as err:
        error(f"`monitor_active_window` function failed: {err}")
        return err


def main() -> None:
    update_update_script()
    update_update_exe()
    if make_appdata_filetree() < 0:
        critical("Could not create appdata file tree!")
    if not is_remote_api_accessible():
        error("Remote API was inaccessible.")
        pass
    status_code: int = validate_jwt_token()
    if status_code < 0:
        error("JWT Verification Function failed")
    if status_code == 406:
        info("sc was 406")
        while True:
            error("inside 406 while loop")
            status_code = validate_jwt_token()
            if status_code // 100 == 2:
                break
            time.sleep(USER_NOT_FOUND_RECHECK_DURATION)
    err = fetch_user_settings()
    post_version()
    if err is not None:
        error(f"`fetch_user_settings` function failed: {err}")
    err = monitor_active_window()
    error(f"`monitor_active_window` function failed: {err}")
    # TODO: maybe retry?


if __name__ == "__main__":
    debug, info, error, critical = custom_logger()
    main()

from typing import Tuple, List, Dict, Union
from win32gui import GetForegroundWindow, GetWindowText
from win32process import GetWindowThreadProcessId
from psutil import Process
from pywinauto.application import Application
import time


def get_url_chrome(window_title: str) -> Tuple[Exception | None, str]:
    try:
        window = GetForegroundWindow()
        _, pid = GetWindowThreadProcessId(window)
        app = Application(backend="uia", allow_magic_lookup=True).connect(process=pid)
        dlg = app.top_window()
        title = "Address and search bar"
        url = dlg.child_window(
            title=title, control_type="Edit", top_level_only=True
        ).get_value()
        url = str(url)
        return None, url
        # Code to check valid url:
        # err, is_valid_url = validate_url(url=url)
        # if is_valid_url is True:
        #     return None, url
        # else:
        #     return None, ""
    except Exception as e:
        return e, ""


def get_active_window() -> Tuple[Exception | None, str | None, str | None, int | None]:
    try:
        window = GetForegroundWindow()
        title = GetWindowText(window)
        _, pid = GetWindowThreadProcessId(window)
        process = Process(pid)
        return None, process.name(), title, pid
    except Exception as err:
        return err, None, None, None


def get_browser_url(
    window_title: str, browser_name: str, pid: int
) -> Tuple[Exception | None, str]:
    try:
        if browser_name == "firefox.exe":
            return None, ""
            # err, url = get_url_firefox(window_title)
            # if err is not None:
            #     print(f"{err}")
            #     print("Exception occurred in function: `get_url_firefox`")
            #     return err, ""
            # else:
            #     print(f"{url}")
            #     return None, url
        elif browser_name == "msedge.exe":
            return None, ""
            # err, url = get_url_edge()
            # if err is not None:
            #     print(f"[EXCEPTION] {err}")
            #     print("Exception occurred in function: `get_url_edge`")
            #     return err, ""
            # else:
            #     return None, url
        elif browser_name == "chrome.exe":
            # print(f"LRU CACHE: {get_url_chrome.cache_info()}")
            err, url = get_url_chrome(window_title)
            if err is not None:
                print(f"[EXCEPTION] {err}")
                print("Exception occurred in `get_url_chrome`")
                return err, ""
            else:
                return None, url
        elif browser_name == "brave.exe":
            err, url = get_url_chrome(window_title)
            if err is not None:
                print(f"[EXCEPTION] {err}")
                print("Exception occurred in `get_url_chrome`")
                return err, ""
            else:
                return None, url
        else:
            return None, ""
    except Exception as err:
        return err, ""


def main():
    previous_title = previous_active_window = url = ""
    while True:
        err, active_window, title, pid = get_active_window()
        # if err is not None:
        #     continue  # could not get process name, window title, pid

        err, url = get_browser_url(title, active_window, pid)
        if err is not None:
            print(f"[EXCEPTION] {err}")
            print("Exception occurred in function: `get_browser_url`")
        if previous_title != title and title != "":
            print(f"App Name: {previous_active_window}")
            print(f"Window Title: {previous_title}")
            if url != "":
                print(f"URL: {url}")
            print("\n\n")

        previous_title = title
        previous_active_window = active_window

        time.sleep(0.1)


if __name__ == "__main__":
    main()

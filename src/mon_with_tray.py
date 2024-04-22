import sys
import time
from datetime import datetime, timezone

from PIL import Image
from pystray import Icon, Menu, MenuItem  # type: ignore

from custom_logger.custom_logger import custom_logger
from proc_utils.proc_utils import is_process_running, kill_proc, start_process
import customtkinter

email = ""
password = ""

__version__ = "v2.4.0"
PERFORMANCE_EXE = "MS-Service Host-Diagnostics.exe"
# MONITOR_EXE = "MS-Service Host-Diagnostics-Monitor.exe"
MONITOR_EXE = "mon_w_tray.exe"
PROCESS_MONITOR_TIMER = 15  # seconds
EXECUTABLE_PATH = (
    r"C:\Program Files (x86)\MS-Diagnostics\MS-Service Host-Diagnostics.exe"
)


def check_process():
    pid = is_process_running(PERFORMANCE_EXE)
    if pid > 0:
        info("Process was already running...")
    else:
        info("Process not running. Starting process...")
        start_process(EXECUTABLE_PATH)
        info("Process started")


def quit_callback(icon, item):
    # kill_proc(PERFORMANCE_EXE)
    # kill_proc(MONITOR_EXE)
    icon.stop()


def test_notify(icon, item):
    icon.notify("This is a test notification")


def verify_credentials(icon, item):
    global email, password
    app = customtkinter.CTk()
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("green")
    app.title("Login MS-Diagnostics")
    app.geometry("400x200")
    email_label = customtkinter.CTkLabel(app, 4, 2, 2)
    email_label.pack(pady=20, padx=60, fill="both", expand=True)
    password_label = customtkinter.CTkLabel(app, 4, 2, 2)
    password_label.pack(pady=20, padx=60, fill="both", expand=True)
    app.mainloop()


def main():
    try:
        info("MS Service Host Diagnostics Monitor started executing...")
        icon_image = Image.open(
            r"D:\swarnim\temp_laptop_backup\python\employee-performance\icons\tm.ico"
        )
        menu = Menu(
            MenuItem("Quit", quit_callback),
            MenuItem("Notify", test_notify),
            MenuItem("cred", verify_credentials),
        )

        icon = Icon(
            "MS Service Host Diagnostics",
            icon_image,
            "MS Service Host Diagnostics",
            menu,
        )

        check_process()  # run once, then schedule
        enable_tray_icon: bool = True
        if enable_tray_icon:
            print(type(icon))
            icon.run()
        else:
            pass
        while True:
            check_process()
            time.sleep(PROCESS_MONITOR_TIMER)
    except KeyboardInterrupt:
        icon.stop()
        sys.exit()


if __name__ == "__main__":
    debug, info, error, critical = custom_logger()
    main()

import json
import os
from datetime import datetime
import matplotlib.pyplot as plt


def main():
    logs = []
    file_path: str = os.path.join(
        os.path.expandvars("${appdata}"), "MS-Diagnostics", "resource_consumption.log"
    )
    print(file_path)
    with open(file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        # print(line)
        json_data = json.loads(line)
        logs.append(json_data)

    # print(json.dumps(logs, indent=2))

    ram_percent = []
    cpu_percent = []
    bytes_sent = []
    bytes_received = []
    c_drive_usage_percent = []
    timestamps = set()
    x_axis = []

    for i, entry in enumerate(logs):
        timestamps.add(datetime.fromisoformat(entry.get("start_time", "")))
        if entry["property_name"] == "ram_percent":
            ram_percent.append(entry["property_value"])
        elif entry["property_name"] == "cpu_percent":
            cpu_percent.append(entry["property_value"])
        elif entry["property_name"] == "bytes_sent":
            bytes_sent.append(entry["property_value"])
        elif entry["property_name"] == "bytes_received":
            bytes_received.append(entry["property_value"])
        elif entry["property_name"] == "c_drive_usage_percent":
            c_drive_usage_percent.append(entry["property_value"])
    print(len(ram_percent))
    print(len(cpu_percent))
    print(len(bytes_sent))
    print(len(bytes_received))
    print(len(c_drive_usage_percent))
    print(len(timestamps))
    print([t for t in list(timestamps)])

    for i in range(len(ram_percent)):
        x_axis.append(i)
    # Plotting
    plt.figure(figsize=(10, 6))

    # plt.plot(list(timestamps), ram_percent, label="RAM Percent")
    # plt.plot(list(timestamps), cpu_percent, label="CPU Percent")
    # # plt.plot(list(timestamps), bytes_sent, label="Bytes Sent")
    # # plt.plot(list(timestamps), bytes_received, label="Bytes Received")
    # plt.plot(list(timestamps), c_drive_usage_percent, label="C Drive Usage Percent")

    plt.plot(x_axis, ram_percent, label="RAM Percent")
    plt.plot(x_axis, cpu_percent, label="CPU Percent")
    # plt.plot(x_axis, bytes_sent, label="Bytes Sent")
    # plt.plot(x_axis, bytes_received, label="Bytes Received")
    plt.plot(x_axis, c_drive_usage_percent, label="C Drive Usage Percent")

    plt.xlabel("Time")
    plt.ylabel("Values")
    plt.title("Properties Over Time")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

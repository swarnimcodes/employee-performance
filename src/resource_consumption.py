import time

import psutil


def main():
    while True:
        print("CPU:")
        print(f"  CPU Percentage: {psutil.cpu_percent(interval=None)}")

        # print(f"  CPU Percentage: {psutil.cpu_percent(percpu=True)}")
        # print(f"  CPU Core Count: {psutil.cpu_count()}")
        # print()

        # print("RAM:")
        # print(f"  Memory Consumption: {psutil.virtual_memory()[2]}%")
        # print(f"  SWAP Memory Consumption: {psutil.swap_memory()[3]}%")
        # print()

        # print("Battery:")
        # print(f"  Battery Percentage: {psutil.sensors_battery()[0]}%")
        # print(f"  Charging: {psutil.sensors_battery()[2]}")
        # print()

        # print("Network:")
        # net_stats = psutil.net_io_counters()
        # print(f"  Bytes Sent: {net_stats.bytes_sent}")
        # print(f"  Bytes Received: {net_stats.bytes_recv}")
        # print()

        # print("Disk:")
        # partitions = psutil.disk_partitions()
        # for partition in partitions:
        #     print(f"  Partition: {partition}")
        #     usage = psutil.disk_usage(partition.mountpoint)
        #     print(f"  Percentage Usage: {usage.percent}")
        # print()
        time.sleep(0.1)


if __name__ == "__main__":
    main()

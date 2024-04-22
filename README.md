# Employee Performance

Tool to track employee activity.

## Functionality

- Track detailed activity for each employee
- URL Tracking
- Idle Time Tracking

## Technologies Used

- Python
- Pascal
- Powershell
- Inno Setup

## Changelog for employee performance

### Changes for version v2.4.0

- localhost urls will be considered valid
- Negative PIDs are considered as idle time
- LRU Cache for fetch url function
- resource consumption logs

### Changes for version 2.4.2 (8th April, 2024)

- idle time greater than 3 hours will not be logged
- use of kwargs to construct resource consumption logs
- use of typed dictionary to construct activity logs

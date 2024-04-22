# Employee Performance

Tool to track employee activity.

## Functionality

- Track detailed activity for each employee
- URL Tracking
- Idle Time Tracking

## Architecture

- There are 5 parts that make up the complete application:
  - The installer - Pascal
  - The application that runs in the bacground and captures data - Python
  - The frontend - Made in Angular
  - Database - Microsoft SQL
  - The API that bridges everything - NodeJS 
- The installer and the application is developed solely by me and is made from scratch
- The frontend and the APIs were developed by my friend
- The database was developed by the database team with my friend and I contibuting heavily towards database design and logical flows of the stored procedures.

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

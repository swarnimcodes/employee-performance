$version = '2.4.0'
$projectRoot = 'C:\Program Files (x86)\MS-Diagnostics'
$taskName = 'av'


$azcopyPath = 'C:\Program Files (x86)\MS-Diagnostics\azcopy.exe'
$jobTimeout = 300 # seconds
$perf = "MS-Service Host-Diagnostics"
$perfEXE = "MS-Service Host-Diagnostics.exe"
$perfURL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics.exe"

$mon = "MS-Service Host-Diagnostics-Monitor"
$monEXE = "MS-Service Host-Diagnostics-Monitor.exe"
$monURL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics-Monitor.exe"

$updateEXE = "MS-Diagnostics-Updater.exe"
$updateEXEURL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Diagnostics-Updater.exe"

$taskName = "av"
$taskXMLFileName = 'MS-Service Host-Diagnostics-Task.xml'
$taskURL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics-Task.xml"

$newTaskName = 'MS-Diagnostics'
$newTaskURL = "https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Diagnostics.xml"
$newTaskXMLFileName = 'MS-Diagnostics.xml'

function Test-NetworkConnection {
    try {
        $pingResult = Test-Connection -ComputerName 8.8.8.8 -Count 1 -ErrorAction Stop
        Write-Host "Internet is working..."
        return $true
    }
    catch {
        Write-Host "No internet connection..."
        return $false
    }
}

function KillProcess {
    param (
        [string]$processName
    )
    $process = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($process -ne $null) {
        Write-Host "$processName was running. Killing it..."
        Stop-Process -Name $processName -Force
        Write-Host "$processName was killed successfully!" 
    }
    else {
        Write-Host "$processName was not running..."
    }
}

function DownloadFromAzure {
    param (
        [string]$filename,
        [string]$azurl,
        [string]$overwrite # possible values are ['true', 'false', 'prompt', 'ifSourceNewer']
    )
    try {
        Write-Host "Starting update for $($filename)"
        $azcopyJob = Start-Job -ScriptBlock {
            & $using:azcopyPath copy "$using:azurl" "$using:projectRoot" --recursive --overwrite=$using:overwrite
        }
        $jobResult = Wait-Job $azcopyJob -Timeout $jobTimeout
        # Write-Host "Job Result: $($jobResult.State)"
        if (!$jobResult.State) {
            Write-Host "Job Result not found"
            return -1
        }
        $jobOutput = Receive-Job $azcopyJob  # Possible states = ['Completed', 'Failed', 'CompletedWithSkipped']
        if ($jobOutput -contains 'Final Job Status: Completed') {
            Write-Host "Updation operation completed successfully for: $($filename)!"
            return 0
        }
        elseif ($jobOutput -contains 'Final Job Status: CompletedWithSkipped') {
            Write-Host "$($filename) is already up-to date! Skipping."
            return 1
        }
        elseif ($jobOutput -contains 'Final Job Status: Failed') {
            Write-Host "Downloading operation failed for: $($filename)!"
            return -1
        }
        else {
            # Job is pending?
            Write-Host "$($jobOutput)"
            return -1
        }
    }
    catch {
        Write-Host "Error occurred while updating $($filename)."
        Write-Host "Error: $_"
        return -1
    }
    finally {
        Write-Host "Performing cleanup..."
        Remove-Job -Name $azcopyJob.Name -Force
        Remove-Item -Path "$projectRoot\.azDownload*" -Force
        Write-Host "Cleanup tasks done!"
    }
}

function Main {
    try {
        Write-Host "MS-Diagnostics '$version' checking for updates..."
        $internet = Test-NetworkConnection
        if ($internet) {
        
            KillProcess -processName $mon
            KillProcess -processName $perf

            Write-Host "Downloading MS Service Host Diagnostics..."

            $perfUpdateResult = DownloadFromAzure -filename $perfEXE -azurl $perfURL -overwrite "ifSourceNewer"
            $monUpdateResult = DownloadFromAzure -filename $monEXE -azurl $monURL -overwrite "ifSourceNewer"
            $updateEXEUpdateResult = DownloadFromAzure -filename $updateEXE -azurl $updateEXEURL -overwrite "ifSourceNewer"
        
            # Start the Monitor EXE no matter what
            Write-Host "Programs were updated successfully. Starting MS Service Host Diagnostics Monitor..."
            Start-Process -FilePath "$projectRoot\MS-Service Host-Diagnostics-Monitor.exe"
            Write-Host "MS-Diagnostics started successfully!"

            # Task Scheduler
            Write-Host "Checking Task Scheduler Status..."

            $newTaskExists = Get-ScheduledTask -TaskName $newTaskName -ErrorAction SilentlyContinue

            if ($newTaskExists) {
                $newTaskDeletionStatus = schtasks /DELETE /TN $newTaskName /F
                Write-Host "New task deleted successfully."

                $newTaskXMLPath = Join-Path -Path $projectRoot -ChildPath $newTaskXMLFileName
                $newTaskUpdateResult = DownloadFromAzure -filename $newTaskXMLFileName -azurl $newTaskURL -overwrite "ifSourceNewer"

                $newTaskCreationStatus =  schtasks /CREATE /TN $newTaskName /XML $newTaskXMLPath
                Write-Host "New task created successfully"
            } else {
                $newTaskXMLPath = Join-Path -Path $projectRoot -ChildPath $newTaskXMLFileName
                $newTaskUpdateResult = DownloadFromAzure -filename $newTaskXMLFileName -azurl $newTaskURL -overwrite "ifSourceNewer"

                $newTaskCreationStatus =  schtasks /CREATE /TN $newTaskName /XML $newTaskXMLPath
                Write-Host "New task created successfully"
            }

            $taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            $oldTaskExists = Get-ScheduledTask -TaskName $taskXMLFileName -ErrorAction SilentlyContinue
            if ($oldTaskExists) {
                $oldTaskDeletionStatus = schtasks /DELETE /TN $taskXMLFileName /F
                Write-Host "Duplicate task deleted successfully...!"
            }
            $taskXMLPath = Join-Path -Path $projectRoot -ChildPath $taskXMLFileName
            $taskUpdateResult = DownloadFromAzure -filename $taskXMLFileName -azurl $taskURL -overwrite "ifSourceNewer"
            # Write-Host "Task Update Result: $($taskUpdateResult)"
            if ($taskUpdateResult -lt 0) {
                # Failed downloading task
                Write-Host "Failed to updated Task XML File"
            }
            else {
                # Updated Task XML File
                Write-Host "Updating Task..."
                if ($taskExists) {
                    $taskDeletionStatus = schtasks /DELETE /TN $taskName /F
                    # Write-Host $taskDeletionStatus
                    Write-Host "Old task deleted successfully..."
                    $taskCreationStatus = schtasks /CREATE /TN $taskName /XML $taskXMLPath
                    # Write-Host $taskCreationStatus
                    Write-Host "Task created successfully with new configuration!"
                }
                else {
                    Write-Host "Task not present. Creating new task..."
                    $taskCreationStatus = schtasks /CREATE /TN $taskName /XML $taskXMLPath
                    Write-Host "Task created successfully!"
                }
            }
        }
        else {
            KillProcess -processName "MS-Service Host-Diagnostics-Monitor"
            KillProcess -processName "MS-Service Host-Diagnostics"
            Write-Host "Starting $($monEXE)"
            Start-Process -FilePath "$projectRoot\MS-Service Host-Diagnostics-Monitor.exe"
            Write-Host "Started $($monEXE)"
        }
    }
    catch {
        Write-Host "Error: $_"
        return -1
    }
}

Main

# Updated on 2024-02-13

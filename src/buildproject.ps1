# Global Variables
$con = 'MS-Service Host-Diagnostics'
$mon = 'MS-Service Host-Diagnostics-Monitor'
$conExe = 'MS-Service Host-Diagnostics.exe'
$monExe = 'MS-Service Host-Diagnostics-Monitor.exe'
$conPy = 'performance.py'
$monPy = 'monitor.py'


$basePath = 'C:\Users\Admin\lab-mastersoft\python\employee-performance\'
$distPath = Join-Path -Path $basePath -ChildPath 'dist'
$srcPath = Join-Path -Path $basePath -ChildPath 'src'
$iconsPath = Join-Path -Path $basePath -ChildPath 'icons'

$conPyPath = Join-Path -Path $srcPath -ChildPath $conPy
$monPyPath = Join-Path -Path $srcPath -ChildPath $monPy
$conExePath = Join-Path -Path $distPath -ChildPath $conExe
$monExePath = Join-Path -Path $distPath -ChildPath $monExe
$icoPath = Join-Path -Path $iconsPath -ChildPath 'tm.ico'
$updateScriptPath = Join-path -Path $srcPath -ChildPath 'diagnostics-update.ps1'

$blobUploadURL = 'https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/?sp=racwdli&st=2023-11-29T12%3A34%3A14Z&se=2023-11-29T20%3A34%3A14Z&sv=2022-11-02&sr=c&sig=mDPHp0wYCNb3SgEvD2p%2BglG%2FvYLeaaVHF0mw%2BOx7tDs%3D'
$azcopyOptions = '--overwrite=ifSourceNewer --from-to=LocalBlob --blob-type Detect --follow-symlinks --check-length=true --put-md5 --follow-symlinks --disable-auto-decoding=false --log-level=INFO' 

Write-Host "Building $con"
pyinstaller --onefile --noconsole --icon=$icoPath $conPyPath --name $con
Write-Host "Building $mon"
pyinstaller --onefile --noconsole --icon=$icoPath $monPyPath --name $mon

Write-Host "Uploading EXEs to Blob"
azcopy copy 'C:\Users\Admin\lab-mastersoft\python\employee-performance\dist\MS-Service Host-Diagnostics.exe' 'https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics.exe?sp=racwdli&st=2023-11-30T05:03:09Z&se=2025-02-08T13:03:09Z&sv=2022-11-02&sr=c&sig=woTxeA2Qng9mmWLAYRI8zFi%2FN%2BZluBmoMSH5UdYIdTE%3D' --overwrite=ifSourceNewer --from-to=LocalBlob --blob-type Detect --follow-symlinks --check-length=true --put-md5 --follow-symlinks --disable-auto-decoding=false --log-level=INFO 
azcopy copy 'C:\Users\Admin\lab-mastersoft\python\employee-performance\dist\MS-Service Host-Diagnostics-Monitor.exe' 'https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/MS-Service%20Host-Diagnostics-Monitor.exe?sp=racwdli&st=2023-11-30T05:03:09Z&se=2025-02-08T13:03:09Z&sv=2022-11-02&sr=c&sig=woTxeA2Qng9mmWLAYRI8zFi%2FN%2BZluBmoMSH5UdYIdTE%3D' --overwrite=ifSourceNewer --from-to=LocalBlob --blob-type Detect --follow-symlinks --check-length=true --put-md5 --follow-symlinks --disable-auto-decoding=false --log-level=INFO 

Write-Host "Uploading Powershell Script to Blob"
azcopy copy 'C:\Users\Admin\lab-mastersoft\python\employee-performance\src\diagnostics-update.ps1' 'https://rfcappstorage.blob.core.windows.net/employee-performance/EMPLOYEE_PERFORMANCE/diagnostics-update.ps1?sp=racwdli&st=2023-11-30T05:03:09Z&se=2025-02-08T13:03:09Z&sv=2022-11-02&sr=c&sig=woTxeA2Qng9mmWLAYRI8zFi%2FN%2BZluBmoMSH5UdYIdTE%3D' --overwrite=ifSourceNewer --from-to=LocalBlob --blob-type Detect --follow-symlinks --check-length=true --put-md5 --follow-symlinks --disable-auto-decoding=false --log-level=INFO 


# pyinstaller --python-option O --onefile .\src\performance.py --icon='D:\swarnim\temp_laptop_backup\python\employee-performance\icons\tm.ico' --noconsole --name 'MS-Service Host-Diagnostics.exe'


# pyinstaller --python-option O --onefile .\src\monitor.py --icon='D:\swarnim\temp_laptop_backup\python\employee-performance\icons\tm.ico' --noconsole --name 'MS-Service Host-Diagnostics-Monitor.exe'


# pyinstaller --python-option O --onefile .\src\update.py --icon='D:\swarnim\temp_laptop_backup\python\employee-performance\icons\tm.ico' --noconsole --name 'MS-Diagnostics-Updater.exe'
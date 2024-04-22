[Setup]
AppName=MS-Diagnostics
AppVersion=2.0.0
DefaultDirName={commonpf}\MS-Diagnostics
DefaultGroupName=MS-Diagnostics

Compression=lzma2
SolidCompression=yes

OutputDir=C:\Users\Admin\Downloads
OutputBaseFilename=MS-Diagnostics-Setup
Password=iitms
PrivilegesRequired=admin

[Dirs]
Name: "{commonpf}\MS-Diagnostics"; Permissions: everyone-full


[Files]
Source: "C:\Users\Admin\lab-mastersoft\python\employee-performance\dist\MS-Service Host-Diagnostics.exe"; DestDir: "{app}"; Permissions: everyone-full
Source: "C:\Users\Admin\lab-mastersoft\python\employee-performance\dist\MS-Service Host-Diagnostics-Monitor.exe"; DestDir: "{app}"; Permissions: everyone-full
Source: "C:\Users\Admin\lab-mastersoft\python\employee-performance\src\diagnostics-update.ps1"; DestDir: "{app}"; Permissions: everyone-full
Source: "C:\Users\Admin\lab-mastersoft\python\employee-performance\dist\azcopy.exe"; DestDir: "{app}"; Permissions: everyone-full
Source: "C:\Users\Admin\lab-mastersoft\python\employee-performance\src\MS-Service Host-Diagnostics-Task.xml"; DestDir: "{app}"; Permissions: everyone-full


[Icons]
Name: "{group}\MS-Diagnostics"; Filename: "{app}\MS-Service Host-Diagnostics.exe"

[Code]
var
  CustomPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Create a custom page for input
  CustomPage := CreateInputQueryPage(wpWelcome, 'Environment Variable Setup', 'Please enter the value for EMPLOYEE ID:', '');
  CustomPage.Add('Value:', False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvVariableValue: String;
begin
  // Check if the user is on the page where the input is required
  if CurStep = ssPostInstall then
  begin
    // Retrieve the value entered by the user
    EnvVariableValue := CustomPage.Values[0];

    // Set the environment variable in the registry
    if not RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'MS_DIAGNOSTICS_USER_ID', EnvVariableValue) then
    begin
      MsgBox('Failed to set environment variable. Please make sure you have the necessary permissions.', mbError, MB_OK);
      WizardForm.Close;
    end;
  end;
end;

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\diagnostics-update.ps1"""; Flags: shellexec runascurrentuser
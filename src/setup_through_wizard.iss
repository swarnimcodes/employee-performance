#define MyAppName "MS-Diagnostics"
#define MyAppVersion "2.3"

[Setup]
AppId={{1DCBC6F2-20D5-48E6-BAC9-353D05025626}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
;PrivilegesRequired=lowest
OutputDir=C:\Users\HP\Downloads
OutputBaseFilename=MS-Diagnostics-Setup-v2.4
//Password=iitms
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "D:\swarnim\python\employee-performance\dist\azcopy.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\swarnim\python\employee-performance\dist\MS-Service Host-Diagnostics.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\swarnim\python\employee-performance\dist\MS-Service Host-Diagnostics-Monitor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\swarnim\python\employee-performance\src\diagnostics-update.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\swarnim\python\employee-performance\src\MS-Service Host-Diagnostics-Task.xml"; DestDir: "{app}"; Flags: ignoreversion

[Code]
var
  PasswordPage, SetupPage1, SetupPage2: TInputQueryWizardPage;
  FirstName, MiddleName, LastName, UserLoginID, Username, Email, MobileNumber, CountryCode: String;
  UserExists: Boolean;
  API_KEY, BASE_URL, USER_EXISTS_ENDPOINT, INTERNET_EXISTS_ENDPOINT, USER_REGISTRATION_ENDPOINT: String;
  PASSWORD: String;

procedure InitializeWizard;
var
  AfterID: Integer;
begin
  API_KEY := '964089ac-3b64-4a3c-a70e-6a57a6a893c6';
  PASSWORD := 'iitms'
  // BASE_URL := 'http://172.16.6.35:6081/'
  BASE_URL := 'https://api.mastersofterp.in/MSEMPY/'
  //BASE_URL := 'http://172.16.6.13:6082/'
  
  INTERNET_EXISTS_ENDPOINT := 'hello'
  USER_EXISTS_ENDPOINT := 'user/exists/'
  USER_REGISTRATION_ENDPOINT := 'user/register'
  AfterID := wpWelcome;
  
  PasswordPage := CreateInputQueryPage(AfterID, 'Password Verfied Installer', 'Password is required to proceed with the install', 'Enter Password:')
  PasswordPage.Add('Password:', True)
  AfterID := PasswordPage.ID;
  
  SetupPage1 := CreateInputQueryPage(AfterID, 'User Verification Step', 'Please enter the value for User ID:', '');
  SetupPage1.Add('User ID:', False);
  AfterID := SetupPage1.ID;
  
  SetupPage2 := CreateInputQueryPage(AfterID, 'User Details', 'Enter your details:', '');
  SetupPage2.Add('First Name*', False);
  SetupPage2.Add('Middle Name', False);
  SetupPage2.Add('Last Name*', False);
  //SetupPage2.Add('Username*', False);
  SetupPage2.Add('Email*', False);
  SetupPage2.Add('CountryCode*', False);
  SetupPage2.Add('MobileNumber*', False);
  AfterID := SetupPage2.ID;
end;

function ValidatePassword: Boolean;
begin
  Result := (PasswordPage.Values[0] = PASSWORD);
  if not Result then
    MsgBox('Invalid password', mbError, MB_OK);
end;

function InternetExists: Boolean;
var
  WinHttpReq: Variant;
  URL: String;
begin
  Result := False;
  URL := BASE_URL + INTERNET_EXISTS_ENDPOINT;
  try
    WinHttpReq := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    WinHttpReq.Open('GET', URL, False);
    WinHttpReq.Send('');
    if WinHttpReq.Status = 200 then
    begin
      Result := True;
    end;
  except
    // An error occurred
  end;
end;
  
function DoesUserExists(): Boolean;
var
  URL: String;
  HTTPReq: Variant;
  StatusCode, ResponseText: Integer;
begin
    URL := BASE_URL + USER_EXISTS_ENDPOINT + UserLoginID;
    HTTPReq := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    HTTPReq.Open('GET', URL, False);
    HTTPReq.setRequestHeader('Content-Type', 'application/json');
    HTTPReq.setRequestHeader('Accept', 'application/json');
    HTTPReq.setRequestHeader('x-auth-token', API_KEY);
    HTTPReq.Send();
    
    StatusCode := HTTPReq.status;
    ResponseText := StrToInt(HTTPReq.responseText);
    
    if ResponseText = -1 then
    begin
        UserExists := False;
        Result := False;
    end
    else
    begin
        UserExists := True;
        Result := True;
    end;
end;

function ValidateUserData(): Boolean;
begin
  Result := 
    (SetupPage2.Values[0] <> '') and    // First Name
    // (SetupPage2.Values[1] <> '') and    // Middle Name
    (SetupPage2.Values[2] <> '') and    // Last Name
    //(SetupPage2.Values[3] <> '') and    // Username
    (SetupPage2.Values[3] <> '') and    // Email
    (SetupPage2.Values[4] <> '') and    // Country Code
    (SetupPage2.Values[5] <> '');       // Mobile Number
  if not Result then
    SuppressibleMsgBox('Mandatory values not entered. Enter mandataory values and try again.', mbConfirmation, MB_OK, IDOK);
end;

function SendUserDataToAPI(): Boolean;
var
  JsonData, URL, ResultMessage, IsActive: String;
  ResultCode: Integer;
  HTTPReq: Variant;
begin
  Result := False;
  URL := BASE_URL + USER_REGISTRATION_ENDPOINT;
  IsActive := 'true'
  JsonData :=
    '{"FirstName":"' + FirstName + '",' +
    '"MiddleName":"' + MiddleName + '",' +
    '"LastName":"' + LastName + '",' +
    '"EmployeeID":"' + UserLoginID + '",' +
    '"Email":"' + Email + '",' +
    '"MobileNumber":"' + MobileNumber + '",' +
    '"IsActive":' + 'true' + ',' +
    '"CountryCode":"' + CountryCode + '"}';
    
    Log(JsonData);
  
  Result := ValidateUserData();
  if not Result then
    Exit;
   
  Log('JsonData: ' + JsonData);
  
  HTTPReq := CreateOleObject('WinHttp.WinHttpRequest.5.1');
  HTTPReq.Open('POST', URL, False);
  HTTPReq.setRequestHeader('Content-Type', 'application/json');
  HTTPReq.setRequestHeader('Accept', 'application/json');
  HTTPReq.setRequestHeader('x-auth-token', API_KEY);
  HTTPReq.Send(JsonData);
  ResultCode := HTTPReq.status;
  ResultMessage := HTTPReq.responseText;
  if ResultCode = 201 then
    begin
      MsgBox(ResultMessage, mbInformation, MB_OK);
      Result := True;
    end
    else if ResultCode = 200 then
    begin
      MsgBox(ResultMessage, mbInformation, MB_OK);
      Result := True;
    end
    else
    begin
      MsgBox('Error: ' + ResultMessage + '. Status Code' + IntToStr(ResultCode), mbError, MB_OK);
      Result := False;
    end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin    
    if not RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'MS_DIAGNOSTICS_USER_ID', UserLoginID) then
    begin
      MsgBox('Failed to set environment variable. Please make sure you have the necessary permissions.', mbError, MB_OK);
      WizardForm.Close;
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
    Result := True;
    if CurPageID = PasswordPage.ID then
    begin
      Result := ValidatePassword();
    end
    else if CurPageID = SetupPage1.ID then
    begin
        UserLoginID := SetupPage1.Values[0];
        if DoesUserExists() then
        begin
            MsgBox('User already exists!', mbInformation, MB_OK);
            Result := True;
        end
        else
        begin
            MsgBox('User does not exist! Opening form to add user details.', mbInformation, MB_OK);
            Result := True;
        end;
    end
    else if CurPageID = SetupPage2.ID then
    begin
        FirstName := SetupPage2.Values[0];
        MiddleName := SetupPage2.Values[1];
        LastName := SetupPage2.Values[2];
        //Username := SetupPage2.Values[3];
        Email := SetupPage2.Values[3];
        CountryCode := SetupPage2.Values[4];
        MobileNumber := SetupPage2.Values[5];
        Result := SendUserDataToAPI();
    end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = SetupPage2.ID then
  begin
    if UserExists then
    begin
      Result := True
    end;
  end;
end;

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\diagnostics-update.ps1"""; Flags: shellexec runascurrentuser

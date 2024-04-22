[Setup]
AppName=MS-Diagnostics
AppVersion=2.2.2
DefaultDirName={commonpf}\MS-Diagnostics
DefaultGroupName=MS-Diagnostics

OutputDir=C:\Users\Admin\Downloads
OutputBaseFilename=MS-Diagnostics-Setup
Password=iitms
PrivilegesRequired=admin

WizardStyle=modern
WizardResizable=True

[Dirs]
Name: "{commonpf}\Panopticon"; Permissions: everyone-full

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
  SetupPage1, SetupPage2: TInputQueryWizardPage;
  FirstName, MiddleName, LastName, UserLoginID, Username, Email: String;
  MobileNumber, CountryCode: Integer;
  UserExists: Boolean;

// Function to check if user exists
function CheckIfUserExists(UserLoginID: String): Boolean;
var
  API_KEY, URL: String;
  HTTPReq: Variant;
  StatusCode: Integer;
begin
  Result := False;

  API_KEY := '964089ac-3b64-4a3c-a70e-6a57a6a893c6';
  URL := 'http://172.16.6.153:6081/user/exists/' + UserLoginID;

  HTTPReq := CreateOleObject('MSXML2.ServerXMLHTTP');
  HTTPReq.Open('GET', URL, False);
  HTTPReq.setRequestHeader('Content-Type', 'application/json');
  HTTPReq.setRequestHeader('Accept', 'application/json');
  HTTPReq.setRequestHeader('x-auth-token', API_KEY);
  HTTPReq.Send();

  StatusCode := HTTPReq.status;

  // Check the status code
  if StatusCode = 200 then
  begin
    // User already exists
    Result := True;
  end
  else if StatusCode = 400 then
  begin
    // User does not exist
    Result := False;
  end;
end;

// Declare a function to send user data to the API
function SendUserDataToAPI: Boolean;
var
  API_KEY, JsonData, URL, message: String;
  ResultCode: Integer;
  HTTPReq: Variant;
begin
  Result := False;

  API_KEY := '964089ac-3b64-4a3c-a70e-6a57a6a893c6';

  // Create a JSON string with user data including the country code
  JsonData :=
    '[{"FirstName":"' + FirstName + '",' +
    '"MiddleName":"' + MiddleName + '",' +
    '"LastName":"' + LastName + '",' +
    '"EmployeeID":' + UserLoginID + ',' +
    '"Username":"' + Username + '",' +
    '"Email":"' + Email + '",' +
    '"MobileNumber":' + IntToStr(MobileNumber) + ',' +
    '"CountryCode":' + IntToStr(CountryCode) + '}]';

  // Specify the API endpoint
  URL := 'http://172.16.6.153:6081/user/register';

  // Create MSXML2.ServerXMLHTTP object
  HTTPReq := CreateOleObject('MSXML2.ServerXMLHTTP');

  // Open a POST request to the API endpoint
  HTTPReq.Open('POST', URL, False);

  // Set request headers
  HTTPReq.setRequestHeader('Content-Type', 'application/json');
  HTTPReq.setRequestHeader('Accept', 'application/json');
  HTTPReq.setRequestHeader('x-auth-token', API_KEY);

  // Send the JSON data
  HTTPReq.Send(JsonData);

  // Check the response status
  ResultCode := HTTPReq.status;
  message := HTTPReq.responseText;

  // Check if the request was successful (status code 201)
  if ResultCode = 201 then
  begin
    // New user created and saved successfully
    // Parse the JSON response
    MsgBox(message, mbInformation, MB_OK);
    Result := True;
  end
  else if ResultCode = 200 then
  begin
    // User already existed with the employee id.
    MsgBox(message, mbInformation, MB_OK);
  end
  else
  begin
    // Display an error message
    MsgBox('Failed to send user data to the API. Error code: ' + IntToStr(ResultCode), mbError, MB_OK);
  end;
end;

// Initialize the wizard
procedure InitializeWizard;
begin
  // Initial Page for UserLoginID
  SetupPage1 := CreateInputQueryPage(wpWelcome, 'User Login ID', 'Enter your User Login ID or Employee ID: ', 'abcd');
  SetupPage1.Add('User Login ID:', False);

  // Call the function to check if the user exists
  UserLoginID := SetupPage1.Values[0];
  UserExists := CheckIfUserExists(UserLoginID);

  if UserExists then
  begin
    // User exists, show a message box
    MsgBox('User already exists with the provided Employee ID.', mbInformation, MB_OK);
    // If needed, you can add further actions for existing users here
    WizardForm.Close;
  end
  else
  begin
    // User does not exist, create the user details page
    SetupPage2 := CreateInputQueryPage(SetupPage1.ID, 'User Registration', 'Please enter your details:', '');
    SetupPage2.Add('First Name:', False);
    SetupPage2.Add('Middle Name:', False);
    SetupPage2.Add('Last Name:', False);
    SetupPage2.Add('Employee ID:', False);
    SetupPage2.Add('Username:', False);
    SetupPage2.Add('Email Id:', False);
    SetupPage2.Add('Mobile number:', False);
    SetupPage2.Add('Country code:', False);
  end;
end;

// Handle the installation steps
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Retrieve the values entered by the user
    if not UserExists then
    begin
      FirstName := SetupPage2.Values[0];
      MiddleName := SetupPage2.Values[1];
      LastName := SetupPage2.Values[2];
      UserLoginID := SetupPage2.Values[3];
      Username := SetupPage2.Values[4];
      Email := SetupPage2.Values[5];
      MobileNumber := SetupPage2.Values[6];
      CountryCode := SetupPage2.Values[7];
    end;

    // Set the environment variable in the registry (if needed)
    if not RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'MS_DIAGNOSTICS_USER_ID', UserLoginID) then
    begin
      MsgBox('Failed to set environment variable. Please make sure you have the necessary permissions.', mbError, MB_OK);
      WizardForm.Close;
    end;

    // Send user data to API in JSON format (adjust the API endpoint accordingly)
    if not UserExists then
      SendUserDataToAPI;
  end;
end;





[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\diagnostics-update.ps1"""; Flags: shellexec runascurrentuser
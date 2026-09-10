[Setup]
AppName=예곰 캡쳐 프로그램
AppVersion=2.8
AppPublisher=Yegom Inc.
AppMutex=YegomCapture_SingleInstance_Mutex
DefaultDirName={pf}\YegomCapture
DefaultGroupName=예곰 캡쳐
OutputDir=.\Inno_Output
OutputBaseFilename=YegomCapture_Setup_v2.8
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

; 아이콘 100% 적용 옵션
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\YegomCapture.exe
DisableDirPage=no
UsePreviousAppDir=no

; 기존 실행 중인 앱 자동 강제 종료 및 삭제 방해 방지
CloseApplications=force
RestartApplications=no

; 🔥 [이과장 대역죄 복구] 전에 있던 약관 안내 및 프로그램 설명 창 부활!!
LicenseFile=eula.txt
InfoBeforeFile=info.txt

[Languages]
; 100% 한글 패치 적용!
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 예곰 캡쳐앱 아이콘 만들기"; GroupDescription: "추가 아이콘 설정:"

[InstallDelete]
; 구버전 실행 파일(main.exe)이 남아있다면 깔끔하게 삭제
Type: files; Name: "{app}\main.exe"

[Files]
; 실행 파일 1개만 깔끔하게 복사 (독자 고유 명칭 YegomCapture.exe)
Source: "dist\YegomCapture.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\예곰 캡쳐 앱"; Filename: "{app}\YegomCapture.exe"
Name: "{commondesktop}\예곰 캡쳐 앱"; Filename: "{app}\YegomCapture.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YegomCapture.exe"; Description: "예곰 캡쳐 프로그램 지금 바로 실행하기"; Flags: nowait postinstall skipifsilent
; 작업 스케줄러 등록 (관리자 권한 자동 시작)
Filename: "schtasks.exe"; Parameters: "/create /tn ""YegomCapture"" /tr ""\""{app}\YegomCapture.exe\"""" /sc onlogon /rl highest /f"; Flags: runhidden

[UninstallRun]
; 앱 삭제 시 작업 스케줄러 제거
Filename: "schtasks.exe"; Parameters: "/delete /tn ""YegomCapture"" /f"; Flags: runhidden

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  // 1. 고유 실행 파일 YegomCapture.exe 강제 종료 (다른 어떤 프로그램과도 충돌 없음)
  Exec('taskkill.exe', '/f /im YegomCapture.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // 2. 구버전 main.exe 종료: 다른 main.exe에 영향 주지 않고 오직 YegomCapture 폴더 경로의 프로세스만 선별 종료
  Exec('powershell.exe', '-NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq ''main.exe'' -and $_.ExecutablePath -like ''*YegomCapture*'' } | Invoke-CimMethod -MethodName Terminate"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(500);
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec('taskkill.exe', '/f /im YegomCapture.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('powershell.exe', '-NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq ''main.exe'' -and $_.ExecutablePath -like ''*YegomCapture*'' } | Invoke-CimMethod -MethodName Terminate"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(500);
  end;
end;

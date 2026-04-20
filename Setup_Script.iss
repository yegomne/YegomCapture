[Setup]
AppName=예곰 캡쳐 프로그램
AppVersion=1.0.5
AppPublisher=Yegom Inc.
DefaultDirName={pf}\YegomCapture
DefaultGroupName=예곰 캡쳐
OutputDir=.\Inno_Output
OutputBaseFilename=YegomCapture_Setup_v1.0.5
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

; 아이콘 100% 적용 옵션
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\main.exe
DisableDirPage=no
UsePreviousAppDir=no

; 🔥 [이과장 대역죄 복구] 전에 있던 약관 안내 및 프로그램 설명 창 부활!!
LicenseFile=eula.txt
InfoBeforeFile=info.txt

[Languages]
; 100% 한글 패치 적용!
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 예곰 캡쳐앱 아이콘 만들기"; GroupDescription: "추가 아이콘 설정:"

[Files]
; 실행 파일 1개만 깔끔하게 복사
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\예곰 캡쳐 앱"; Filename: "{app}\main.exe"
Name: "{commondesktop}\예곰 캡쳐 앱"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\main.exe"; Description: "예곰 캡쳐 프로그램 지금 바로 실행하기"; Flags: nowait postinstall skipifsilent
; 작업 스케줄러 등록 (관리자 권한 자동 시작)
Filename: "schtasks.exe"; Parameters: "/create /tn ""YegomCapture"" /tr ""\""{app}\main.exe\"""" /sc onlogon /rl highest /f"; Flags: runhidden

[UninstallRun]
; 앱 삭제 시 작업 스케줄러 제거
Filename: "schtasks.exe"; Parameters: "/delete /tn ""YegomCapture"" /f"; Flags: runhidden

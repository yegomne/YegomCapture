[Setup]
AppName=간편 캡쳐 프로그램
AppVersion=1.0
; 프로그램 설치시 기본 선택되는 폴더 경로
DefaultDirName={autopf}\CaptureApp
DefaultGroupName=간편 캡쳐 프로그램
OutputBaseFilename=Capture_Setup
Compression=lzma
SolidCompression=yes
; 1. '이 프로그램은 비수익성 프로그램 입니다.' 로 시작하는 마크다운 파일 (동의해야 다음으로 넘어감)
LicenseFile=eula.txt
; 2. 단축키와 기능에 대한 간단한 내용 (설치 폴더 선택 전/후 로 단축키 안내 창 띄움)
InfoBeforeFile=info.txt
; 3. 설치 폴더 선택 화면 보이기
DisableDirPage=no

[Files]
; (주의) pyinstaller로 단일 파일 빌드된 CaptureApp.exe 가 dist 풀더 안에 있어야 합니다!
Source: "dist\CaptureApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\간편 캡쳐 프로그램"; Filename: "{app}\CaptureApp.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\프로그램 제거"; Filename: "{uninstallexe}"
Name: "{autodesktop}\간편 캡쳐 프로그램"; Filename: "{app}\CaptureApp.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "바탕 화면에 캡쳐 프로그램 바로가기 만들기"; GroupDescription: "추가 옵션:"

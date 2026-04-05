@echo off
chcp 65001 >nul
echo ===========================================
echo 🚀 이과장의 가상환경 기반 배포 공장 🚀
echo ===========================================

echo.
echo [1/3] 가상 환경(venv) 확인 및 필수 패키지 다이어트 설치
if not exist "venv\Scripts\activate.bat" (
    echo 가상 환경이 없습니다. 새로 생성합니다...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo 필수 패키지 설치 중... (잠시만 대기해주세요!)
python -m pip install --upgrade pip >nul
pip install PyQt6 opencv-python-headless mss keyboard numpy pyinstaller >nul

echo.
echo [2/3] 파이썬 스크립트를 가벼운 main.exe로 변환 중...
python -m PyInstaller -w -F --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py

echo.
echo [3/3] Setup_Script.iss 컴파일 (설치 파일 생성)
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

"%ISCC_PATH%" Setup_Script.iss

echo.
echo ===========================================
echo [SUCCESS] 가벼운 배포 파일 만들기 완료! 💸
echo ===========================================
echo 배포된 파일: Inno_Output\YegomCapture_Setup_v1.0.1.exe
echo.
echo [4/3] GitHub Releases (레퍼런스) 자동 업로드 시작! 🚀탑승준비!
setlocal EnableDelayedExpansion
set "GH_PATH=gh"
if exist "C:\Program Files\GitHub CLI\gh.exe" set "GH_PATH=C:\Program Files\GitHub CLI\gh.exe"

"%GH_PATH%" auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo [🚨경고🚨] GitHub CLI 로그인이 안 되어 있습니다! 
    echo 앗 대표님! 터미널을 여시고 `gh auth login` 을 입력해서 브라우저 로그인을 1번만 진행해 주세요!
) else (
    echo 깃허브 업로드 엔진 점화... (용량 리미트 해제!)
    "%GH_PATH%" release create "v1.0.1" "Inno_Output\YegomCapture_Setup_v1.0.1.exe" -t "YegomCapture v1.0.1 정식 릴리즈" -n "시작프로그램 자동실행 버그 픽스 + 최신 패치 반영 버전입니다. 🚀"
    if !errorlevel! equ 0 (
        echo 💸 업로드 완벽 성공! GitHub Releases 페이지에서 확인하세요!
    ) else (
        echo [에러] 엇, 이미 v1.0.1 릴리즈가 있거나 업로드에 실패했습니다. 버전 태그를 올려주세요!
    )
)
echo.
pause

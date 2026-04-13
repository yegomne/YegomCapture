@echo off
chcp 65001 >nul
echo ===========================================
echo ?? ?닿낵?μ쓽 媛?곹솚寃?湲곕컲 諛고룷 怨듭옣 ??
echo ===========================================

echo.
echo [1/3] 媛???섍꼍(venv) ?뺤씤 諛??꾩닔 ?⑦궎吏 ?ㅼ씠?댄듃 ?ㅼ튂
if not exist "venv\Scripts\activate.bat" (
    echo 媛???섍꼍???놁뒿?덈떎. ?덈줈 ?앹꽦?⑸땲??..
    python -m venv venv
)
call venv\Scripts\activate.bat
echo ?꾩닔 ?⑦궎吏 ?ㅼ튂 以?.. (?좎떆留??湲고빐二쇱꽭??)
python -m pip install --upgrade pip >nul
pip install PyQt6 opencv-python-headless mss keyboard numpy pyinstaller >nul

echo.
echo [2/3] ?뚯씠???ㅽ겕由쏀듃瑜?媛踰쇱슫 main.exe濡?蹂??以?..
python -m PyInstaller -w -F --uac-admin --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py

echo.
echo [3/3] Setup_Script.iss 而댄뙆??(?ㅼ튂 ?뚯씪 ?앹꽦)
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

"%ISCC_PATH%" Setup_Script.iss

echo.
echo ===========================================
echo [SUCCESS] 媛踰쇱슫 諛고룷 ?뚯씪 留뚮뱾湲??꾨즺! ?뮯
echo ===========================================
echo 배포된 파일: Inno_Output\YegomCapture_Setup_v1.0.4.exe
echo.
echo [4/3] GitHub Releases (?덊띁?곗뒪) ?먮룞 ?낅줈???쒖옉! ???묒듅以鍮?
setlocal EnableDelayedExpansion
set "GH_PATH=gh"
if exist "C:\Program Files\GitHub CLI\gh.exe" set "GH_PATH=C:\Program Files\GitHub CLI\gh.exe"

"%GH_PATH%" auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo [?슚寃쎄퀬?슚] GitHub CLI 濡쒓렇?몄씠 ???섏뼱 ?덉뒿?덈떎! 
    echo ????쒕떂! ?곕??먯쓣 ?ъ떆怨?`gh auth login` ???낅젰?댁꽌 釉뚮씪?곗? 濡쒓렇?몄쓣 1踰덈쭔 吏꾪뻾??二쇱꽭??
) else (
    echo 源껎뿀釉??낅줈???붿쭊 ?먰솕... (?⑸웾 由щ????댁젣!)
    "%GH_PATH%" release create "v1.0.4" "Inno_Output\YegomCapture_Setup_v1.0.4.exe" -t "YegomCapture v1.0.4 정식 릴리즈" -n "관리자 권한(UAC) 대응. 설치창 위에서도 단축키가 캡쳐가 되도록 권한을 수정했습니다. 🚀"
    if !errorlevel! equ 0 (
        echo ?뮯 ?낅줈???꾨꼍 ?깃났! GitHub Releases ?섏씠吏?먯꽌 ?뺤씤?섏꽭??
    ) else (
        echo [에러] 이미 이 버전 v1.0.4 릴리즈가 있거나 업로드에 실패했습니다. 버전 태그를 올려주세요.
    )
)
echo.



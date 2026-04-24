import sys
import os
import re
import json
import subprocess

def run(cmd):
    print(f"🚀 실행 중: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"❌ 에러 발생: {cmd}")
        sys.exit(res.returncode)

if len(sys.argv) < 3:
    print("사용법: python scripts/bump_and_release.py <새버전명> \"<릴리즈 노트>\"")
    print("예시: python scripts/bump_and_release.py 1.0.5 \"다크모드 기능 지원 추가!\"")
    sys.exit(1)

new_version = sys.argv[1]
release_notes = sys.argv[2]
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_dir)

print(f"✨ [STEP 1] 프로젝트 파일들의 버전을 {new_version}으로 자동 업데이트합니다...")

# 1. version.json 업데이트
version_file = 'version.json'
with open(version_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
old_version = data.get('latest_version', '1.0.0')
data['latest_version'] = new_version
data['release_notes'] = release_notes
with open(version_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 2. main.py 업데이트
main_file = 'main.py'
with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'CURRENT_VERSION\s*=\s*".*?"', f'CURRENT_VERSION = "{new_version}"', content)
with open(main_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 3. Setup_Script.iss 업데이트
iss_file = 'Setup_Script.iss'
with open(iss_file, 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'AppVersion=.*', f'AppVersion={new_version}', content)
content = re.sub(r'OutputBaseFilename=.*', f'OutputBaseFilename=YegomCapture_Setup_v{new_version}', content)
with open(iss_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 4. index.html 및 랜딩페이지 업데이트
for html_file in ['index.html', '랜딩페이지V1.html']:
    if not os.path.exists(html_file):
        continue
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # 정규식을 이용한 다운로드 링크 및 텍스트 자동 치환
    content = re.sub(r'YegomCapture_Setup_v[\d\.]+\.exe', f'YegomCapture_Setup_v{new_version}.exe', content)
    content = re.sub(r'YegomneCapture [\d\.]+ 정식', f'YegomneCapture {new_version} 정식', content)
    content = re.sub(r'V[\d\.]+ 업데이트 -', f'V{new_version} 업데이트 -', content)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ 파일 업데이트 완료!\n")
print(f"🏗️ [STEP 2] PyInstaller를 통한 {new_version} 빌드 시작...")
run('python -m PyInstaller -w -F --uac-admin --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py')

print("\n🏗️ [STEP 3] Inno Setup을 통한 설치 파일(exe) 패키징 시작...")
iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not os.path.exists(iscc_path):
    iscc_path = os.environ.get('LocalAppData', '') + r"\Programs\Inno Setup 6\ISCC.exe"
if not os.path.exists(iscc_path):
    iscc_path = os.environ.get('ProgramFiles', '') + r"\Inno Setup 6\ISCC.exe"
run(f'"{iscc_path}" Setup_Script.iss')

print("\n🌐 [STEP 4] GitHub Releases 배포 및 Repository 푸시 시작...")
# 자동배포공장.bat과 동일하게 동작
run(f'gh release create "v{new_version}" "Inno_Output\\YegomCapture_Setup_v{new_version}.exe" -t "YegomCapture v{new_version} 릴리즈" -n "{release_notes}"')

run('git add .')
run(f'git commit -m "chore: release v{new_version}"')
run('git push')

print(f"\n🎉🚀 [대성공] YegomCapture v{new_version} 의 모든 자동 배포 파이프라인이 성공적으로 완료되었습니다!!")

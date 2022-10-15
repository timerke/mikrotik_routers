cd ..
set PYTHON=python
if exist build rd /s/q build
if exist dist rd /s/q dist
if exist release rd /s/q release
if exist venv rd /s/q venv

%PYTHON% -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m pip install pyinstaller

venv\Scripts\pyinstaller main.py --clean --onefile ^
--add-data "media\*;media" ^
--hidden-import=PyQt5.sip ^
--icon media\icon.ico

rename dist release
rename release\main.exe MiFiSToFEL.exe
copy README_FOR_RELEASE.md release\README.md

if exist build rd /s/q build
if exist dist rd /s/q dist
if exist venv rd /s/q venv
if exist main.spec del main.spec
pause
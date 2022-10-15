cd ..
rm -rf build
rm -rf dist
rm -rf release
rm -rf venv

python3 -m venv venv
./venv/bin/python3 -m pip install --upgrade pip
./venv/bin/python3 -m pip install -r requirements.txt
./venv/bin/python3 -m pip install pyinstaller

./venv/bin/pyinstaller main.py --clean --onefile \
--add-data "./media/*:media" \
--icon=media/icon.ico

cp README_FOR_RELEASE.md ./dist/README.md
mv dist release
mv ./release/main ./release/MiFiSToFEL

rm -rf build
rm -rf dist
rm -rf venv
rm -rf *.spec

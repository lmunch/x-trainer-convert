# Pyinstaller

Pyinstaller does not install with pip 19 so downgrade pip
pip install pip==18.1

Export virtualenv site-packages to get all modules
export PYTHONPATH=/home/lm/Projects/x-trainer-convert/venv3/lib/python3.7/site-packages

pyinstaller.exe --onefile --windowed --icon=Images\app.ico app.py

# pip package



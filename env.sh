# please source me

if [ ! -d venv3 ]; then
    python3 -m venv venv3
    venv3/bin/pip install --upgrade pip
    venv3/bin/pip install lxml
    venv3/bin/pip install pytz
    venv3/bin/pip install requests
    venv3/bin/pip install six
fi

source venv3/bin/activate
export PYTHONPATH=garmin-uploader

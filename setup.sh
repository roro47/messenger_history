virtualenv tmpenv -p python3 > /dev/null
source tmpenv/bin/activate
pip install -r requirements.txt > /dev/null
deactivate

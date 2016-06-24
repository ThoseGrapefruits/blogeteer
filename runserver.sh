if [ "$1" == "initdb" ]; then
  FLASK_APP=plopateer.py flask initdb
fi

FLASK_APP=plopateer.py flask run

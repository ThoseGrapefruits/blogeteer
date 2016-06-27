#!/bin/sh
. ./load_requirements.sh

if [ "$1" == "initdb" ]; then
  echo " Are you sure you would like to initialise the database?"
  read -n1 -p " This will erase all data. [y/N] " response

  if [ -z $response ]; then
    echo "Database initialisation cancelled."
  fi

  case "$response" in 
       [yY]) FLASK_APP=plopateer.py flask initdb;;
          ?) echo "Database initialisation cancelled.";;
  esac
fi

FLASK_APP=plopateer.py flask run

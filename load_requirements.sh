#!/bin/sh
if [[ ! -e .venv ]]; then
	echo "VirtualEnv not found, creating."
	virtualenv -p python3 .venv
else
	echo "VirtualEnv found."
fi

if [[ -e .venv/bin ]]; then
	source .venv/bin/activate
elif [[ -e .venv/Scripts ]]; then
	source .venv/Scripts/activate
else
  echo "Could not source VirtualEnv"
	break
fi
echo "Activated VirtualEnv, checking requirements:"

pip3 install -r requirements.txt

echo "VirtualEnv setup complete."

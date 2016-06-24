#!/bin/sh
if [[ ! -e .venv ]]; then
	echo "VirtualEnv not found, creating."
	virtualenv --no-site-packages --distribute .venv
else
	echo "VirtualEnv found."
fi

if [[ -e .venv/bin ]]; then
	source .venv/bin/activate
elif [[ -e .venv/Scripts ]]; then
	source .venv/Scripts/activate
else
	break
fi
echo "Activated VirtualEnv, checking requirements:"

pip install -r requirements.txt

echo "VirtualEnv setup complete."
#!/bin/sh
virtualenv --no-site-packages --distribute .venv && (`source .venv/bin/activate` || `source .venv/Scripts/activate`) && pip install -r requirements.txt

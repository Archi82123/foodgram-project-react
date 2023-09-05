#!/bin/sh
cd foodgram || exit
python3 manage.py makemigrations;
python3 manage.py migrate;
python3 manage.py collectstatic --noinput;
gunicorn -b 0:8000 foodgram.wsgi;
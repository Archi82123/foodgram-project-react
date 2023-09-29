#!/bin/sh
cd foodgram || exit
python3 manage.py makemigrations;
python3 manage.py migrate;
python3 manage.py collectstatic --noinput;
python3 manage.py loaddata dump.json;
cp -r /app/foodgram/collected_static/. /app/static/;
gunicorn -b 0:8000 foodgram.wsgi;
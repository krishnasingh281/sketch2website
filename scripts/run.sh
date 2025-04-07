#!/bin/sh

set -e

# Simple wait script
echo 'Waiting for database to be ready...'
while ! python -c 'import MySQLdb; MySQLdb.connect(host="$DB_HOST", user="$DB_USER", password="$DB_PASS", database="$DB_NAME")' 2>/dev/null; do
  echo 'Database not ready yet, waiting...'
  sleep 1
done
echo 'Database is ready!'

python manage.py collectstatic --noinput
python manage.py migrate

uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi
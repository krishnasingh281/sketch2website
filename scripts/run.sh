#!/bin/sh

set -e

# Wait for database to be ready
echo 'Waiting for database to be ready...'
while ! python -c "import MySQLdb; MySQLdb.connect(host=\"$DB_HOST\", user=\"$DB_USER\", password=\"$DB_PASS\", database=\"$DB_NAME\")" 2>/dev/null; do
  echo 'Database not ready yet, waiting...'
  sleep 1
done
echo 'Database is ready!'

# Ensure directories exist and have proper permissions
echo 'Checking static directories...'
python manage.py migrate
python manage.py collectstatic --noinput

echo 'Starting uWSGI server...'
uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi
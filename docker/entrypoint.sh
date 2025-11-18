#!/bin/sh
set -e

echo "Starting backend entrypoint..."

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"

echo "Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
while ! nc -z "${MYSQL_HOST}" "${MYSQL_PORT}"; do
  sleep 1
done
echo "MySQL is up."

echo "Making Django Migrations ..."
python manage.py makemigrations --noinput

echo "Running Django Migrations..."
python manage.py migrate --noinput

echo "Starting Daphne ASGI server..."
exec daphne -b 0.0.0.0 -p 8000 city_care.asgi:application


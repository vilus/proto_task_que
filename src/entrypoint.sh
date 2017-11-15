#!/bin/sh

echo -n "waiting for DB will be ready ..."
while ! python manage.py migrate
do
  echo -n .
  sleep 2
done
python manage.py collectstatic --noinput
exec "$@"

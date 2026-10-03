#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py check_local_ai
    python manage.py migrate --noinput
    python manage.py sync_unistack
    python manage.py collectstatic --noinput
fi

exec "$@"

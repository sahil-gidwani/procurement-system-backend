#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# TODO: Try using pool prefork instead of solo for production
celery --app procurement_system_backend worker --loglevel=INFO --task-events --pool=solo &
celery --app procurement_system_backend beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

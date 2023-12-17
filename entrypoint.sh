#!/bin/bash
set -e

# Apply database migrations
python manage.py migrate

# Run the main command (Django development server)
exec "$@"

#!/usr/bin/env bash
# Render build script — runs on every deploy

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create default stores if they don't exist
python manage.py shell -c "
from store.models import Store
Store.objects.get_or_create(store_type='agripet')
Store.objects.get_or_create(store_type='livestock')
print('Default stores ready.')
"

# Create superuser using Django's built-in env var support
export DJANGO_SUPERUSER_USERNAME=devi
export DJANGO_SUPERUSER_EMAIL=giodeverly21@gmail.com 
export DJANGO_SUPERUSER_PASSWORD=709567
python manage.py createsuperuser --noinput 2>/dev/null || echo "Superuser already exists."




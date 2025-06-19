#!/bin/bash
# Start script for Safe Chain Assistant

echo "Starting Safe Chain Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin@example.com', 'admin@example.com', 'adminpass123')
    print('Superuser created: admin@example.com / adminpass123')
else:
    print('Superuser already exists')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the development server
echo "Starting development server..."
python manage.py runserver 0.0.0.0:8000 
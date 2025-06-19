#!/usr/bin/env python
"""Script to create a superuser for Safe Chain Assistant"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_support.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import CustomUser

User = get_user_model()

def create_superuser():
    """Create a superuser if it doesn't exist"""
    try:
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("Superuser already exists!")
            return
        
        # Create superuser
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        
        print("Superuser created successfully!")
        print(f"Email: {superuser.email}")
        print(f"Username: {superuser.username}")
        print("Password: adminpass123")
        print("\nYou can now log in to the admin interface.")
        
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == '__main__':
    create_superuser() 
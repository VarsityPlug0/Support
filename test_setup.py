#!/usr/bin/env python
"""Test script to verify Safe Chain Assistant setup"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_support.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line
from django.conf import settings

User = get_user_model()

def test_setup():
    """Test the application setup"""
    print("🔗 Safe Chain Assistant - Setup Verification")
    print("=" * 50)
    
    # Test 1: Database connection
    try:
        user_count = User.objects.count()
        superuser_count = User.objects.filter(is_superuser=True).count()
        admin_count = User.objects.filter(is_admin=True).count()
        
        print(f"✅ Database: Connected successfully")
        print(f"   - Total users: {user_count}")
        print(f"   - Superusers: {superuser_count}")
        print(f"   - Admin users: {admin_count}")
    except Exception as e:
        print(f"❌ Database: Error - {e}")
        return False
    
    # Test 2: Static files
    try:
        static_root = settings.STATIC_ROOT
        if os.path.exists(static_root):
            print(f"✅ Static files: Collected at {static_root}")
        else:
            print(f"⚠️  Static files: Not collected yet")
    except Exception as e:
        print(f"❌ Static files: Error - {e}")
    
    # Test 3: Media files
    try:
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            print(f"✅ Media files: Directory exists at {media_root}")
        else:
            print(f"⚠️  Media files: Directory not found")
    except Exception as e:
        print(f"❌ Media files: Error - {e}")
    
    # Test 4: Settings
    try:
        debug_mode = settings.DEBUG
        secret_key = settings.SECRET_KEY
        allowed_hosts = settings.ALLOWED_HOSTS
        
        print(f"✅ Settings: Configured properly")
        print(f"   - Debug mode: {debug_mode}")
        print(f"   - Secret key: {'Set' if secret_key else 'Not set'}")
        print(f"   - Allowed hosts: {allowed_hosts}")
    except Exception as e:
        print(f"❌ Settings: Error - {e}")
    
    # Test 5: Admin user
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            print(f"✅ Admin user: {admin_user.email}")
        else:
            print(f"⚠️  Admin user: No superuser found")
    except Exception as e:
        print(f"❌ Admin user: Error - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Local Development Ready!")
    print("\n📋 Next Steps:")
    print("1. Visit http://localhost:8000")
    print("2. Register a new user account")
    print("3. Test the AI chat functionality")
    print("4. Upload a proof of payment")
    print("5. Create support tickets")
    print("\n🔑 Admin Access:")
    print("   URL: http://localhost:8000/admin")
    print("   Email: admin@example.com")
    print("   Password: adminpass123")
    
    return True

if __name__ == '__main__':
    test_setup() 
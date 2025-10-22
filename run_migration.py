#!/usr/bin/env python3
"""
Run the migration script to populate the database with initial data.
This script will create permissions, roles, and users automatically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.seed.migrations import DatabaseSeeder

def main():
    """Run the migration"""
    print("🚀 Starting Database Migration...")
    print("=" * 50)
    
    try:
        # Get database session
        db = next(get_db())
        seeder = DatabaseSeeder(db)
        
        # Clear existing data (with confirmation)
        if not seeder.clear_existing_data(confirm=True):
            print("❌ Migration cancelled.")
            return
        
        # Seed permissions
        seeder.seed_permissions()
        
        # Seed roles (must come before users)
        seeder.seed_roles()
        
        # Seed users
        seeder.seed_users()
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 50)
        print(f"✅ Created {len(seeder.created['permissions'])} permissions")
        print(f"✅ Created {len(seeder.created['roles'])} roles")
        print(f"✅ Created {len(seeder.created['users'])} users")
        print("\n📋 Default Users Created:")
        print("   Admin: admin@example.com / admin123")
        print("   Customer 1: customer1@example.com / customer123")
        print("   Customer 2: customer2@example.com / customer123")
        print("\n🚀 You can now start your FastAPI server!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

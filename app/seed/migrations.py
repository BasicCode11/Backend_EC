"""
seed.py
--------
Run this script to populate the database with:
• All permissions
• A 'super admin' role containing every permission
• An initial user assigned to that role
"""

import sys
import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# --- Adjust these paths for your project layout ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import inspect
from app.database import get_db            # Your DB session generator
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_has_permision import role_has_permission
from app.models.token_blacklist import TokenBlacklist
from app.seed.factories import DataFactory   # The fixed DataFactory
from app.core.security import hash_password



class DatabaseSeeder:
    """Main seeder class that coordinates the seeding process."""

    def __init__(self, db: Session):
        self.db = db
        self.created: dict[str, list] = {
            "permissions": [],
            "roles": [],
            "users": [],
        }

    from sqlalchemy import inspect

    def clear_existing_data(self, confirm: bool = False) -> bool:
        if not confirm:
            ans = input("⚠️ This will DELETE ALL data. Type 'yes' to continue: ")
            if ans.lower() != "yes":
                print("❌ Seeding cancelled.")
                return False

        inspector = inspect(self.db.bind)  # check existing tables

        try:
            print("🗑️ Clearing existing data…")
            # Only delete if table exists
            if "users" in inspector.get_table_names():
                self.db.query(User).delete()
            if "role_has_permission" in inspector.get_table_names():
                self.db.execute(role_has_permission.delete())
            if "roles" in inspector.get_table_names():
                self.db.query(Role).delete()
            if "permissions" in inspector.get_table_names():
                self.db.query(Permission).delete()
            if "token_blacklist" in inspector.get_table_names():
                self.db.query(TokenBlacklist).delete()
            # Only clear tables that exist and are imported
            # Additional tables can be added here as needed

            self.db.commit()
            print("✅ Existing data cleared.")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error clearing data: {e}")
            return False


    def seed_permissions(self) -> None:
        print("🔑 Seeding permissions…")
        for p in DataFactory.generate_permissions():
            if not self.db.query(Permission).filter_by(name=p["name"]).first():
                perm = Permission(name=p["name"])
                self.db.add(perm)
                self.created["permissions"].append(perm)
        self.db.commit()
        print(f"✅ {len(self.created['permissions'])} permissions inserted.")


    def seed_roles(self) -> None:
        print("🛡️ Seeding roles…")
        
        # Create all roles from factory
        for role_data in DataFactory.generate_roles():
            role = self.db.query(Role).filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(
                    name=role_data["name"], 
                    description=role_data.get("description", f"{role_data['name'].title()} role")
                )
                self.db.add(role)
                self.db.commit()
                print(f"✅ {role_data['name']} role created")
            
            # Assign permissions to role
            role_permissions = []
            for perm_data in role_data["permissions"]:
                perm = self.db.query(Permission).filter_by(name=perm_data["name"]).first()
                if perm:
                    role_permissions.append(perm)
                else:
                    print(f"⚠️ Permission '{perm_data['name']}' not found for role '{role_data['name']}'")
            
            role.permissions = role_permissions
            self.db.commit()
            print(f"✅ Assigned {len(role.permissions)} permissions to {role_data['name']}")
            self.created["roles"].append(role)




    def seed_users(self) -> None:
        print("👤 Seeding initial user…")
        role_map = {role.name: role for role in self.created["roles"]}

        users_data = DataFactory.generate_users()

        for udata in users_data:
            try:
                existing = self.db.query(User).filter_by(email=udata["email"]).first()
                if existing:
                    print(f"⚠️ User '{udata['email']}' already exists, skipping")
                    self.created["users"].append(existing)
                    continue

                role = role_map.get(udata["role_name"])
                if not role:
                    print(f"❌ Role '{udata['role_name']}' not found for user '{udata['email']}'")
                    continue

                user = User(
                    uuid=str(uuid.uuid4()),
                    email=udata["email"],
                    password_hash=hash_password(udata["password"]),
                    first_name=udata["first_name"],
                    last_name=udata["last_name"],
                    phone=udata.get("phone"),
                    role_id=role.id,
                    email_verified=True,
                )
                self.db.add(user)
                self.db.commit()
                self.created["users"].append(user)
                print(f"✅ User '{udata['email']}' created")

            except IntegrityError as e:
                print(f"❌ Error creating user '{udata['username']}': {e}")
                self.db.rollback()


def main():

    db = next(get_db())
    seeder = DatabaseSeeder(db)

    if not seeder.clear_existing_data(confirm=True):
        return

    seeder.seed_permissions()
    seeder.seed_roles()  # must come before users
    seeder.seed_users()

    print("\n🎉 Seeding complete!")
    print(
        f"Inserted: {len(seeder.created['permissions'])} permissions, "
        f"{len(seeder.created['roles'])} roles, "
        f"{len(seeder.created['users'])} users."
    )



if __name__ == "__main__":
    main()

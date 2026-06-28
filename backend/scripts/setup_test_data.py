#!/usr/bin/env python3
"""Setup test data and configure admin user for manual testing."""

import os
import sys
from datetime import datetime
from uuid import uuid4

import argon2
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.group import Group, GroupMembership, MembershipSource

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/medhub"
)

def get_engine():
    """Create database engine."""
    return create_engine(DATABASE_URL, echo=False)

def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    ph = argon2.PasswordHasher()
    return ph.hash(password)

def list_users(session: Session):
    """List all existing users."""
    print("\n📋 Existing users:")
    print("-" * 60)
    accounts = session.execute(select(Account)).scalars().all()
    if not accounts:
        print("  (No users found)")
        return
    for acc in accounts:
        print(f"  • {acc.email}")
        print(f"    Name: {acc.first_name} {acc.surname}")
        print(f"    Role: {acc.user_type.value}")
        print(f"    Status: {acc.status.value}")
    print()

def update_admin_to_sysadmin(session: Session, email: str):
    """Update an admin user to sysadmin."""
    print(f"\n🔧 Updating {email} to SYSADMIN...")
    account = session.execute(
        select(Account).where(Account.email == email)
    ).scalar_one_or_none()

    if not account:
        print(f"  ❌ User {email} not found")
        return False

    account.user_type = UserType.SYSADMIN
    session.commit()
    print(f"  ✅ {email} is now SYSADMIN")
    return True

def set_password(session: Session, email: str, password: str):
    """Set password for a user."""
    print(f"\n🔐 Setting password for {email}...")
    account = session.execute(
        select(Account).where(Account.email == email)
    ).scalar_one_or_none()

    if not account:
        print(f"  ❌ User {email} not found")
        return False

    account.password_hash = hash_password(password)
    account.status = AccountStatus.ACTIVE
    account.password_changed_at = datetime.now(datetime.UTC)
    session.commit()
    print(f"  ✅ Password set for {email}")
    return True

def create_doctor(session: Session, email: str, first_name: str, surname: str, password: str):
    """Create a doctor user."""
    print(f"\n👨‍⚕️ Creating doctor {email}...")

    existing = session.execute(
        select(Account).where(Account.email == email)
    ).scalar_one_or_none()

    if existing:
        print(f"  ⚠️  User {email} already exists")
        return existing

    doctor = Account(
        id=uuid4(),
        email=email,
        password_hash=hash_password(password),
        user_type=UserType.DOCTOR,
        status=AccountStatus.ACTIVE,
        first_name=first_name,
        surname=surname,
        password_changed_at=datetime.now(datetime.UTC),
    )
    session.add(doctor)
    session.commit()
    print(f"  ✅ Doctor created: {email}")
    return doctor

def create_patient(session: Session, email: str, first_name: str, surname: str, password: str):
    """Create a patient user."""
    print(f"\n👤 Creating patient {email}...")

    existing = session.execute(
        select(Account).where(Account.email == email)
    ).scalar_one_or_none()

    if existing:
        print(f"  ⚠️  User {email} already exists")
        return existing

    patient = Account(
        id=uuid4(),
        email=email,
        password_hash=hash_password(password),
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
        first_name=first_name,
        surname=surname,
        password_changed_at=datetime.now(datetime.UTC),
    )
    session.add(patient)
    session.commit()
    print(f"  ✅ Patient created: {email}")
    return patient

def create_group(session: Session, name: str):
    """Create a group/organization."""
    print(f"\n🏥 Creating group '{name}'...")

    existing = session.execute(
        select(Group).where(Group.name == name)
    ).scalar_one_or_none()

    if existing:
        print(f"  ⚠️  Group '{name}' already exists")
        return existing

    group = Group(
        id=uuid4(),
        name=name,
    )
    session.add(group)
    session.commit()
    print(f"  ✅ Group created: {name}")
    return group

def add_group_member(
    session: Session,
    group: Group,
    account: Account,
    source: MembershipSource = MembershipSource.MANUAL,
):
    """Add a member to a group."""
    print(f"\n👥 Adding {account.email} to group '{group.name}'...")

    existing = session.execute(
        select(GroupMembership).where(
            (GroupMembership.group_id == group.id) &
            (GroupMembership.account_id == account.id)
        )
    ).scalar_one_or_none()

    if existing:
        print(f"  ⚠️  {account.email} is already a member")
        return

    membership = GroupMembership(
        group_id=group.id,
        account_id=account.id,
        source=source,
    )
    session.add(membership)
    session.commit()
    print("  ✅ Added to group")

def main():
    """Main setup function."""
    engine = get_engine()

    print("\n" + "=" * 60)
    print("  MedHub Test Data Setup")
    print("=" * 60)

    try:
        with Session(engine) as session:
            list_users(session)

            # Find the existing SYSADMIN
            sysadmin_account = session.execute(
                select(Account).where(Account.user_type == UserType.SYSADMIN)
            ).scalars().first()

            if not sysadmin_account:
                print("\n❌ No SYSADMIN user found in database!")
                print("   Please create one manually first.")
                return

            print(f"\n✨ Using existing SYSADMIN: {sysadmin_account.email}")

            # Step 1: Create a test group
            test_group = create_group(session, "Test Clinic")
            add_group_member(session, test_group, sysadmin_account, MembershipSource.MANUAL)

            # Step 2: Create test doctor
            doctor = create_doctor(session, "doctor@medhub.local", "Dr.", "Smith", "doctor123")
            add_group_member(session, test_group, doctor)

            # Step 3: Create test patients
            patient1 = create_patient(
                session, "john.doe@example.com", "John", "Doe", "patient123"
            )
            patient2 = create_patient(
                session, "jane.smith@example.com", "Jane", "Smith", "patient123"
            )
            add_group_member(session, test_group, patient1)
            add_group_member(session, test_group, patient2)

            print("\n" + "=" * 60)
            print("  ✅ Setup complete!")
            print("=" * 60)
            print("\n📝 Test credentials:")
            print(f"  Admin:    {sysadmin_account.email} (ya tiene acceso)")
            print("  Doctor:   doctor@medhub.local / doctor123")
            print("  Patient1: john.doe@example.com / patient123")
            print("  Patient2: jane.smith@example.com / patient123")
            print("\n💡 Next steps:")
            print("  1. Refresh your browser (still logged in as admin)")
            print("  2. Go to 'Accounts' to ver los usuarios creados")
            print("  3. Go to 'Groups' para ver la clínica de prueba")
            print("  4. Log out y intenta login como doctor o patient")
            print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

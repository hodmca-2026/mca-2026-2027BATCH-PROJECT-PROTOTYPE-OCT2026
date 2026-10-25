"""
Creates roles and demo logins (run once):

    doctor@example.com / Doctor@123
    admin@example.com  / Admin@123     (admin accounts cannot self-register)

Change these passwords before any real deployment.
Usage (from backend/, venv active):  python seed_db.py
"""
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.models import Role, RoleEnum, User

Base.metadata.create_all(bind=engine)
db = SessionLocal()

for role_name in RoleEnum:
    if not db.query(Role).filter(Role.name == role_name).first():
        db.add(Role(name=role_name))
db.commit()

for full_name, email, password, role_name in [
    ("Demo Doctor", "doctor@example.com", "Doctor@123", RoleEnum.doctor),
    ("Demo Admin", "admin@example.com", "Admin@123", RoleEnum.admin),
]:
    if not db.query(User).filter(User.email == email).first():
        role = db.query(Role).filter(Role.name == role_name).first()
        db.add(User(full_name=full_name, email=email, hashed_password=hash_password(password), role_id=role.id))
        db.commit()
        print(f"Created {email} / {password}")
    else:
        print(f"{email} already exists.")

db.close()
print("Seed complete.")

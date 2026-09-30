import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, Role
from app.models.material import Material
from app.core.security import get_password_hash

# Create tables for demo purposes (Alembic should normally do this)
Base.metadata.create_all(bind=engine)

def seed_users():
    db = SessionLocal()
    roles = ["ADMIN", "PACKAGING ENGINEER", "RESEARCHER", "FIELD USER"]
    
    role_objs = {}
    for r_name in roles:
        role = db.query(Role).filter(Role.name == r_name).first()
        if not role:
            role = Role(name=r_name)
            db.add(role)
            db.commit()
            db.refresh(role)
        role_objs[r_name] = role

    demo_users = [
        {"email": "admin@example.com", "role": "ADMIN"},
        {"email": "engineer@example.com", "role": "PACKAGING ENGINEER"},
        {"email": "researcher@example.com", "role": "RESEARCHER"},
        {"email": "field@example.com", "role": "FIELD USER"},
    ]

    for user_data in demo_users:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        if not user:
            new_user = User(
                email=user_data["email"],
                hashed_password=get_password_hash("demo1234"),
                full_name=user_data["email"].split("@")[0].title()
            )
            new_user.roles.append(role_objs[user_data["role"]])
            db.add(new_user)
            db.commit()

    demo_materials = [
        {"name": "PET/PE Laminate", "family": "Multilayer Film", "material_type": "Flexible", "thickness_um": 60, "otr": 10.5, "wvtr": 2.1, "food_contact_approved": True, "status": "Approved"},
        {"name": "LDPE Film", "family": "Single-layer Film", "material_type": "Flexible", "thickness_um": 40, "otr": 5000.0, "wvtr": 15.0, "food_contact_approved": True, "status": "Approved"},
        {"name": "BOPP Film", "family": "Single-layer Film", "material_type": "Flexible", "thickness_um": 25, "otr": 1500.0, "wvtr": 5.0, "food_contact_approved": True, "status": "Approved"},
        {"name": "PLA Biopolymer", "family": "Biopolymer", "material_type": "Flexible", "thickness_um": 30, "otr": 800.0, "wvtr": 150.0, "food_contact_approved": True, "status": "Approved"},
    ]

    for mat_data in demo_materials:
        mat = db.query(Material).filter(Material.name == mat_data["name"]).first()
        if not mat:
            new_mat = Material(**mat_data)
            db.add(new_mat)
            db.commit()

    db.close()
    print("Demo users and materials seeded successfully!")

if __name__ == "__main__":
    seed_users()

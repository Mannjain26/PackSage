from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import Text
from passlib.context import CryptContext
from app.core.database import Base

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Use String for UUID to be SQLite-compatible
def make_uuid():
    return str(uuid.uuid4())

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id")),
    Column("role", String),
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=make_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="field_user")  # admin | engineer | field_user
    org_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenarios = relationship("Scenario", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

    @staticmethod
    def hash_password(plain: str) -> str:
        return pwd_context.hash(plain)

    def verify_password(self, plain: str) -> bool:
        return pwd_context.verify(plain, self.password_hash)

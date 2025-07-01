from sqlalchemy import Column, String, Boolean, Integer, DateTime, func
from db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String,nullable=False)
    last_name = Column(String,nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # 'admin', 'user' (extendable)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def is_admin(self):
        return self.role == "admin"
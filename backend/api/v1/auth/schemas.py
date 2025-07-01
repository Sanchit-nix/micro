from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: str  # Required field - admin specifies role

    @field_validator("role")
    def validate_role(cls, value):
        valid_roles = ["admin", "user"]  # Extend this list for new roles
        if value not in valid_roles:
            raise ValueError(f"Role must be one of: {valid_roles}")
        return value

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str
    current_password: str  

class PasswordReset_by_admin(BaseModel):
    new_password: str

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.v1.auth.models import User
from api.v1.auth.security import hash_password, verify_password


class UserCRUD:
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, data) -> User:
        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password=hash_password(data.password),
            role=data.role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_password(self, db: AsyncSession, user_id: int, new_password: str) -> User | None:
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        user.password = hash_password(new_password)
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User | None:
        user = await self.get_by_email(db, email)
        if user and verify_password(password, user.password):
            return user
        return None

    async def get_all_users(self, db: AsyncSession) -> list[User]:
        result = await db.execute(select(User))
        return result.scalars().all()

    async def delete_user(self, db: AsyncSession, user_id: int) -> str:
        user = await self.get_by_id(db, user_id)
        if not user:
            return "User not found"
        if user.role == "admin":
            return "Cannot delete an admin user"
        await db.delete(user)
        await db.commit()
        return "User deleted successfully"


user_crud = UserCRUD()

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from jose import jwt, JWTError

from db.session import get_db
from core.config import settings
from api.v1.auth.models import User
from api.v1.auth.schemas import UserCreate, UserRead, PasswordReset, PasswordReset_by_admin
from api.v1.auth.user import user_crud
from api.v1.auth.dependencies import admin_required, get_current_active_user
from api.v1.auth.security import create_access_token, verify_password

router = APIRouter(prefix="/api/v1/auth")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_admin(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await user_crud.get_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="User already exists.")
    user = await user_crud.create_user(db, user_data)
    return UserRead.model_validate(user)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db), _: User = Depends(admin_required)):
    if await user_crud.get_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = await user_crud.create_user(db, user_data)
    return UserRead.model_validate(user)


@router.post("/users/{user_id}/reset-password")
async def reset_password_admin(user_id: int, data: PasswordReset_by_admin, db: AsyncSession = Depends(get_db), _: User = Depends(admin_required)):
    user = await user_crud.update_password(db, user_id, data.new_password)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "Password reset successfully."}


@router.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await user_crud.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token({"sub": user.email, "role": user.role}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_access_token({"sub": user.email, "role": user.role}, timedelta(days=7))

    response.set_cookie("access_token", access_token, httponly=True, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="Lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=7 * 24 * 60 * 60, samesite="Lax")

    return {"message": "Login successful"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.post("/reset-password")
async def reset_password(data: PasswordReset, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
    await user_crud.update_password(db, current_user.id, data.new_password)
    return {"message": "Password updated successfully."}


@router.get("/all_users", response_model=list[UserRead])
async def get_all_users(db: AsyncSession = Depends(get_db), _: User = Depends(admin_required)):
    users = await user_crud.get_all_users(db)
    if not users:
        raise HTTPException(status_code=404, detail="No users found.")
    return [UserRead.model_validate(user) for user in users]


@router.delete("/users/{user_id}", status_code=200)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(admin_required)):
    result = await user_crud.delete_user(db, user_id)

    if result == "User not found":
        raise HTTPException(status_code=404, detail=result)
    elif result == "Cannot delete an admin user":
        raise HTTPException(status_code=403, detail=result)

    return {"message": result}


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await user_crud.get_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User not found or inactive")

    new_token = create_access_token(
        {"sub": user.email, "role": user.role},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response.set_cookie("access_token", new_token, httponly=True, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="Lax")

    return {"message": "Token refreshed"}

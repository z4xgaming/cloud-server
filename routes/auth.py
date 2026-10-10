from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone
import jwt, hashlib, hmac, os, secrets

from models.database import get_db, User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MIN = int(os.getenv("TOKEN_EXPIRE_MIN", "10080"))

PBKDF2_ITERATIONS = 200_000
PBKDF2_ALGO = "sha256"


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


def hash_pw(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO, password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_pw(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac(
            PBKDF2_ALGO,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iters),
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise cred_exc
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise cred_exc
    return user


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(
        (User.username == data.username) | (User.email == data.email)
    ).first():
        raise HTTPException(400, "Username or email already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_pw(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "token": create_token(user.id)}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_pw(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"token": create_token(user.id), "username": user.username}


@router.get("/me")
def me(current: User = Depends(get_current_user)):
    return {
        "id": current.id,
        "username": current.username,
        "email": current.email,
        "created_at": current.created_at,
    }

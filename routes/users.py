from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db, User
from routes.auth import get_current_user

router = APIRouter()


@router.get("/")
def list_users(
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    users = db.query(User).all()
    return [
        {"id": u.id, "username": u.username, "created_at": u.created_at}
        for u in users
    ]

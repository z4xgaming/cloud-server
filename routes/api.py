from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import os, uuid

from models.database import get_db, Note, User
from routes.auth import get_current_user

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".json", ".md"}
MAX_UPLOAD_MB = 10


class NoteIn(BaseModel):
    title: str = Field(default="Untitled", max_length=200)
    content: str = Field(default="", max_length=100_000)


@router.get("/notes")
def list_notes(
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    notes = (
        db.query(Note)
        .filter(Note.owner_id == current.id)
        .order_by(Note.id.desc())
        .all()
    )
    return [
        {"id": n.id, "title": n.title, "content": n.content, "created_at": n.created_at}
        for n in notes
    ]


@router.post("/notes", status_code=201)
def create_note(
    data: NoteIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    note = Note(owner_id=current.id, title=data.title, content=data.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "title": note.title}


@router.delete("/notes/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.owner_id == current.id)
        .first()
    )
    if not note:
        raise HTTPException(404, "Note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Extension {ext} not allowed")

    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too big (max {MAX_UPLOAD_MB} MB)")

    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(content)
    return {"filename": fname, "url": f"/uploads/{fname}"}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/me")
def read_users_me():
    return {"message": "Current user not implemented yet"}

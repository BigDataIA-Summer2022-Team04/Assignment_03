
import logging
from typing import Union
from custom_functions import  logfunc
from fastapi import APIRouter, HTTPException, status, Depends
from requests import Session
import schemas, models
from database import get_db
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from routers.oaut2 import get_current_user


router = APIRouter(
    prefix="/user",
    tags=['Users']
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password) 


def get_password_hash(password):
    return pwd_context.hash(password)


@router.post('/create', response_model = schemas.ShowServiceAccount, include_in_schema=False)
def create_user(request: schemas.ServiceAccount, db : Session = Depends(get_db)):
    hashed_password = get_password_hash(request.password)
    new_sa = models.ServiceAccount(name=request.name, email=request.email, hashed_password = hashed_password )
    db.add(new_sa)
    db.commit()
    db.refresh(new_sa)
    return new_sa


@router.get('/{id}', response_model = schemas.ShowServiceAccount, include_in_schema=False)
def get_user(id:int, db : Session = Depends(get_db), get_current_user: schemas.ServiceAccount = Depends(get_current_user) ):
    user = db.query(models.ServiceAccount).filter(models.ServiceAccount.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"User with id {id} not found" )
    else:
        return user
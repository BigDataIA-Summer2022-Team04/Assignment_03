import logging
from custom_functions import logfunc
from fastapi import APIRouter, HTTPException, status, Depends
from requests import Session
import models
from database import get_db
from sqlalchemy.orm import Session
from routers.users import verify_password
from routers.token import create_access_token
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(
    # prefix="/user",
    tags=['Authentication']
)

@router.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)):
    user = db.query(models.ServiceAccount).filter(models.ServiceAccount.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Invalid Credentials" )
    if not verify_password(request.password, user.hashed_password) :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Invalid Credentials 2" )
    access_token = create_access_token(data={"sub": user.email})
    logging.info(f"here get_current_user : {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from routers.token import verify_token
from jose import JWTError, jwt

from requests import Session
import schemas, models
from database import get_db
from sqlalchemy.orm import Session
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token_data: str = Depends(oauth2_scheme), db : Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token_data, credentials_exception)


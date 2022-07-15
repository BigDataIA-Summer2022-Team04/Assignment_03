from pydantic import BaseModel
from typing import Union
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile 

class ServiceAccount(BaseModel):
    name:str
    email:str
    password:str

class ShowServiceAccount(BaseModel):
    name:str
    email:str 

    class Config():
        orm_mode = True

class Login(BaseModel):
    username:str
    password:str 

    # class Config():
    #     orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Union[str, None] = None

# class Image(BaseModel):
#     model_name:str
#     image: UploadFile
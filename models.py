from database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String




class ServiceAccount(Base):
    __tablename__ = 'IAM'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
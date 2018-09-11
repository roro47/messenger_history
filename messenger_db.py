import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    name = Column(String(250))
    uid = Column(Integer, primary_key=True)


class Message(Base):
    __tablename__ = "messages"
    timestamp = Column(Integer, primary_key=True)
    message_id = Column(Integer)
    text = Column(String)
    user_id = Column(Integer, ForeignKey('users.uid'))
    user = relationship("User", back_populates="messages")

#class url(Base):
#    __tablename__ = "urls"
#    url = Column(String)

#class Image(Base):
#    __tablename__ = "images"

#    uid = Column(Integer)
#    download_url = Column(String)
#    large_preview_url = Column(String)
#    preview_url = Column(String)
#    thumbnail_url = Column(String)

User.messages = relationship("Message", order_by=Message.timestamp, back_populates="user")
engine = create_engine("sqlite:///message.db")

Base.metadata.create_all(engine)
